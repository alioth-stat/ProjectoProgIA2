"""
Herramienta de documentación: genera explicaciones y docstrings con el LLM.
"""

from __future__ import annotations

from ..infrastructure.llm_client import LLMClient
from ..models import AgentTask, ContextBundle, TaskType, ToolResult
from .base_tool import AgentTool
from .context_builder import ContextBuilder


SYSTEM_EXPLAIN = """\
Eres un experto en programación que explica código de forma clara y didáctica.
Cuando el usuario te muestre código, explica:
1. Qué hace el código en términos de alto nivel.
2. Cómo funciona internamente (lógica principal).
3. Posibles mejoras o puntos de atención.

Usa lenguaje claro. Responde en el mismo idioma que el usuario.
"""

SYSTEM_DOCSTRING = """\
Eres un experto en Python. Tu tarea es generar docstrings completos en formato Google Style
para las funciones o clases que el usuario te pida.

Formato:
\"\"\"Resumen de una línea.

Args:
    param (tipo): Descripción.

Returns:
    tipo: Descripción del valor de retorno.

Raises:
    TipoError: Cuándo se lanza.
\"\"\"

Devuelve SOLO el docstring, sin código adicional.
"""


class DocGeneratorTool(AgentTool):
    """
    Genera explicaciones de código y docstrings automáticos.
    """

    HANDLED_TASKS = {TaskType.EXPLAIN_CODE, TaskType.GENERATE_DOCS}

    def __init__(self, llm: LLMClient, context_builder: ContextBuilder):
        self._llm = llm
        self._ctx_builder = context_builder

    def can_handle(self, task: AgentTask) -> bool:
        return task.tipo in self.HANDLED_TASKS

    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        if task.tipo == TaskType.EXPLAIN_CODE:
            return self.explain_code(task, context)
        return self.generate_docstring(task, context)

    def explain_code(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        ctx_text = self._ctx_builder.format_context_for_prompt(context)
        question = task.input_context.get("question", task.descripcion)
        user_msg = f"{ctx_text}\n\n### Pregunta del usuario\n{question}"

        try:
            explanation = self._llm.complete(system_prompt=SYSTEM_EXPLAIN, user_message=user_msg)
            return ToolResult(success=True, output=explanation)
        except Exception as e:
            return ToolResult(success=False, output=f"Error generando explicación: {e}")

    def generate_docstring(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        code_snippet: str = task.input_context.get("code_snippet", "")
        if not code_snippet:
            # Intenta obtener el código del contexto
            ctx_text = self._ctx_builder.format_context_for_prompt(context)
            code_snippet = ctx_text

        user_msg = f"Genera un docstring para el siguiente código:\n\n```python\n{code_snippet}\n```"

        try:
            docstring = self._llm.complete(system_prompt=SYSTEM_DOCSTRING, user_message=user_msg)
            return ToolResult(success=True, output=docstring)
        except Exception as e:
            return ToolResult(success=False, output=f"Error generando docstring: {e}")
