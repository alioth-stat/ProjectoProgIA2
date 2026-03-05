"""
Herramienta de generación y edición de código usando el LLM.
Maneja tareas de tipo GENERATE_CODE y REFACTOR_CODE.
"""

from __future__ import annotations

from ..infrastructure.llm_client import LLMClient
from ..models import AgentTask, CodePatch, ContextBundle, TaskType, ToolResult
from .base_tool import AgentTool
from .context_builder import ContextBuilder


SYSTEM_PROMPT_GENERATE = """\
Eres un asistente experto en programación. Tu tarea es generar código limpio, \
correcto y bien documentado según las instrucciones del usuario.

Reglas:
- Responde SOLO con el código solicitado, sin explicaciones adicionales a menos que se pidan.
- Usa el mismo lenguaje y estilo que el código existente en el contexto.
- Si el usuario pide una función, devuelve solo esa función.
- Si el usuario pide un archivo completo, devuelve el archivo completo.
- No incluyas ```python``` u otros bloques de markdown a menos que se solicite explícitamente.
"""

SYSTEM_PROMPT_REFACTOR = """\
Eres un experto en refactorización de código. Tu tarea es mejorar el código existente \
manteniendo su funcionalidad intacta.

Reglas:
- Mantén la misma interfaz pública (nombres de funciones/métodos, parámetros).
- Mejora la legibilidad, elimina duplicación y aplica principios SOLID cuando corresponda.
- Devuelve el código refactorizado completo.
- No incluyas bloques de markdown.
"""


class CodeGenerationTool(AgentTool):
    """
    Genera código nuevo o refactoriza código existente usando el LLM.
    """

    HANDLED_TASKS = {TaskType.GENERATE_CODE, TaskType.REFACTOR_CODE}

    def __init__(self, llm: LLMClient, context_builder: ContextBuilder):
        self._llm = llm
        self._ctx_builder = context_builder

    def can_handle(self, task: AgentTask) -> bool:
        return task.tipo in self.HANDLED_TASKS

    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        instruction: str = task.input_context.get("instruction", task.descripcion)
        file_path: str = task.input_context.get("file_path", "output.py")

        context_text = self._ctx_builder.format_context_for_prompt(context)

        if task.tipo == TaskType.GENERATE_CODE:
            system = SYSTEM_PROMPT_GENERATE
            user_msg = f"{context_text}\n\n### Instrucción\n{instruction}"
        else:  # REFACTOR_CODE
            system = SYSTEM_PROMPT_REFACTOR
            guidelines: str = task.input_context.get("guidelines", "")
            user_msg = (
                f"{context_text}\n\n### Guías de refactorización\n{guidelines}\n\n"
                f"Refactoriza el archivo: {file_path}"
            )

        try:
            generated = self._llm.complete(system_prompt=system, user_message=user_msg)
            patch = CodePatch(
                file_path=file_path,
                new_content=generated,
                explanation=f"Generado por {self.name} para la tarea: {task.descripcion}",
            )
            return ToolResult(success=True, output=generated, patches=[patch])
        except Exception as e:
            return ToolResult(success=False, output=f"Error en generación: {e}")
