"""
Clasificador de intención: determina el tipo de tarea a partir del texto del usuario.
Versión inicial basada en palabras clave (sin LLM extra), ampliable a clasificación semántica.
"""

from __future__ import annotations

from ..models import TaskType


# Mapeo de palabras clave → tipo de tarea (orden importa: más específico primero)
INTENT_RULES: list[tuple[list[str], TaskType]] = [
    (["explica", "qué hace", "que hace", "explain", "describe", "como funciona", "cómo funciona"], TaskType.EXPLAIN_CODE),
    (["docstring", "documentación", "documenta", "comenta", "doc"], TaskType.GENERATE_DOCS),
    (["ejecuta", "corre", "run", "lanza", "correr los test", "run tests"], TaskType.RUN_TESTS),
    (["test", "prueba", "unittest", "pytest", "testea"], TaskType.WRITE_TESTS),
    (["analiza", "lint", "flake", "mypy", "errores de tipo", "análisis estático"], TaskType.STATIC_ANALYSIS),
    (["refactoriza", "refactor", "mejora", "limpia", "simplifica"], TaskType.REFACTOR_CODE),
    (["explora", "estructura", "archivos del proyecto", "lista"], TaskType.EXPLORE_CODEBASE),
    (["genera", "crea", "añade", "implementa", "escribe", "generate", "create", "add"], TaskType.GENERATE_CODE),
]

DEFAULT_TASK = TaskType.GENERATE_CODE


class IntentClassifier:
    """
    Determina el TaskType más probable a partir del texto del usuario.
    """

    def classify(self, text: str) -> TaskType:
        text_lower = text.lower()
        for keywords, task_type in INTENT_RULES:
            if any(kw in text_lower for kw in keywords):
                return task_type
        return DEFAULT_TASK
