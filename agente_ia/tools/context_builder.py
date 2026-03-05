"""
ContextBuilder: decide qué fragmentos de código, docs y reglas incluir
en el prompt que se envía al LLM.
"""

from __future__ import annotations

from typing import Optional

from ..models import AgentTask, CodeFile, ContextBundle
from .code_analyzer import CodebaseIndex


MAX_CONTEXT_CHARS = 12_000   # límite conservador para no sobrepasar la ventana del modelo


class ContextBuilder:
    """
    Selecciona el contexto más relevante para una tarea dada.
    Estrategia: archivo activo primero, luego archivos relacionados por nombre/símbolo,
    finalmente reglas del proyecto.
    """

    def __init__(self, index: CodebaseIndex, project_rules: Optional[list[str]] = None):
        self._index = index
        self._rules = project_rules or []

    def build_context(
        self,
        task: AgentTask,
        conversation_summary: str = "",
    ) -> ContextBundle:
        """Construye un ContextBundle relevante para la tarea."""
        selected_files: list[CodeFile] = []
        budget = MAX_CONTEXT_CHARS

        # 1. Archivo activo (si se especificó)
        active_path: Optional[str] = task.input_context.get("file_path")
        if active_path:
            f = self._index.find_file(active_path)
            if f and len(f.content) <= budget:
                selected_files.append(f)
                budget -= len(f.content)

        # 2. Archivos relacionados por palabras clave del description
        keywords = self._extract_keywords(task.descripcion)
        for keyword in keywords:
            for sym in self._index.find_symbol(keyword):
                f = self._index.find_file(sym.file_path)
                if f and f not in selected_files and len(f.content) <= budget:
                    selected_files.append(f)
                    budget -= len(f.content)
                    if budget <= 0:
                        break
            if budget <= 0:
                break

        # 3. Si queda presupuesto, añade archivos pequeños del proyecto
        if budget > 0:
            for f in self._index.files:
                if f not in selected_files and len(f.content) <= budget:
                    selected_files.append(f)
                    budget -= len(f.content)
                    if budget <= 0:
                        break

        return ContextBundle(
            files=selected_files,
            project_rules=self._rules,
            recent_conversation_summary=conversation_summary,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Extrae palabras significativas del texto (mínimo 4 caracteres)."""
        stopwords = {"para", "con", "que", "una", "los", "las", "del", "the", "and", "for", "with"}
        words = [w.strip(".,;:()[]\"'") for w in text.lower().split()]
        return [w for w in words if len(w) >= 4 and w not in stopwords]

    def format_context_for_prompt(self, bundle: ContextBundle) -> str:
        """Serializa el ContextBundle a texto para incluir en el prompt."""
        parts: list[str] = []

        if bundle.recent_conversation_summary:
            parts.append(f"### Historial reciente\n{bundle.recent_conversation_summary}")

        if bundle.project_rules:
            rules_text = "\n".join(f"- {r}" for r in bundle.project_rules)
            parts.append(f"### Reglas del proyecto\n{rules_text}")

        for cf in bundle.files:
            parts.append(f"### Archivo: {cf.path}\n```{cf.language}\n{cf.content}\n```")

        return "\n\n".join(parts)
