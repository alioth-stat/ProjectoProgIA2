"""
AgentOrchestrator: cerebro del agente.
Recibe solicitudes del usuario, las descompone en tareas, las despacha
a los AgentTool adecuados y ensambla la respuesta final.
"""

from __future__ import annotations

from typing import Optional

from ..infrastructure.memory_store import ConversationMemoryStore, ProjectMemoryStore
from ..infrastructure.repository_manager import RepositoryManager
from ..infrastructure.telemetry_logger import TelemetryLogger
from ..models import (
    AgentResponse,
    AgentTask,
    CodePatch,
    ContextBundle,
    TaskStatus,
    TaskType,
    ToolResult,
    UserRequest,
)
from ..tools.base_tool import AgentTool
from ..tools.code_analyzer import CodeAnalyzer, CodebaseIndex
from ..tools.context_builder import ContextBuilder
from .intent_classifier import IntentClassifier


class AgentOrchestrator:
    """
    Coordina el flujo completo: request → plan → dispatch → response.
    """

    def __init__(
        self,
        tools: list[AgentTool],
        context_builder: ContextBuilder,
        code_analyzer: CodeAnalyzer,
        repo_manager: RepositoryManager,
        conversation_memory: ConversationMemoryStore,
        project_memory: ProjectMemoryStore,
        logger: Optional[TelemetryLogger] = None,
        auto_apply_patches: bool = False,
    ):
        self._tools = tools
        self._ctx_builder = context_builder
        self._analyzer = code_analyzer
        self._repo = repo_manager
        self._conv_memory = conversation_memory
        self._proj_memory = project_memory
        self._logger = logger or TelemetryLogger(enabled=False)
        self._auto_apply = auto_apply_patches
        self._classifier = IntentClassifier()

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------

    def handle_request(self, request: UserRequest) -> AgentResponse:
        """Procesa una solicitud del usuario de principio a fin."""
        self._logger.log_user_request(request.text, request.source)
        self._conv_memory.add_turn("user", request.text)

        # 1. Clasificar intención y planificar tareas
        tasks = self.plan_tasks(request)

        if not tasks:
            return AgentResponse(
                message="No pude determinar qué acción tomar. Por favor reformula tu solicitud.",
                success=False,
            )

        # 2. Ejecutar cada tarea
        all_patches: list[CodePatch] = []
        all_outputs: list[str] = []
        overall_success = True

        for task in tasks:
            task.estado = TaskStatus.IN_PROGRESS
            self._logger.log_task_dispatch(task.tipo.value, task.id)

            result = self.dispatch_task(task, request)
            task.resultado = result
            task.estado = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED

            self._logger.log_task_result(task.id, result.success, result.output[:200])

            all_outputs.append(f"[{task.tipo.value}] {result.output}")
            all_patches.extend(result.patches)

            if not result.success:
                overall_success = False

        # 3. Aplicar patches si está en modo autónomo
        if self._auto_apply and all_patches:
            applied = self._repo.apply_patches(all_patches)
            for path in applied:
                self._logger.log_patch_applied(path)

        # 4. Construir respuesta
        message = self._build_response_message(request.text, all_outputs, all_patches)
        self._conv_memory.add_turn("agent", message)
        self._logger.log_agent_response(message)

        return AgentResponse(
            message=message,
            suggested_edits=all_patches,
            success=overall_success,
        )

    # ------------------------------------------------------------------
    # Planificación
    # ------------------------------------------------------------------

    def plan_tasks(self, request: UserRequest) -> list[AgentTask]:
        """
        Determina la lista de AgentTask a ejecutar para satisfacer el request.
        Versión actual: una sola tarea por request (ampliable a multi-step).
        """
        task_type = self._classifier.classify(request.text)

        input_context: dict = {"instruction": request.text}
        if request.file_path:
            input_context["file_path"] = request.file_path
        if request.selection_range:
            input_context["selection_range"] = request.selection_range

        task = AgentTask(
            tipo=task_type,
            descripcion=request.text,
            input_context=input_context,
        )
        return [task]

    # ------------------------------------------------------------------
    # Despacho
    # ------------------------------------------------------------------

    def dispatch_task(self, task: AgentTask, request: UserRequest) -> ToolResult:
        """Selecciona el AgentTool adecuado y ejecuta la tarea."""
        # Construir contexto
        conversation_summary = self._conv_memory.summarize(last_n=6)
        context = self._ctx_builder.build_context(task, conversation_summary)

        # Añadir reglas del proyecto al contexto
        rules = self._proj_memory.as_rules_text()
        context.project_rules.extend(rules)

        # Seleccionar herramienta
        tool = self._select_tool(task)
        if tool is None:
            return ToolResult(
                success=False,
                output=f"No hay herramienta disponible para la tarea: {task.tipo.value}",
            )

        return tool.execute(task, context)

    def _select_tool(self, task: AgentTask) -> Optional[AgentTool]:
        for tool in self._tools:
            if tool.can_handle(task):
                return tool
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_response_message(
        user_text: str,
        outputs: list[str],
        patches: list[CodePatch],
    ) -> str:
        parts = ["\n".join(outputs)]
        if patches:
            patch_list = "\n".join(f"  - {p.file_path}" for p in patches)
            parts.append(f"\nCambios propuestos en:\n{patch_list}")
        return "\n".join(parts)
