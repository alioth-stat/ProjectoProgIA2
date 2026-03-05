"""
Interfaz base que deben implementar todos los AgentTool.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import AgentTask, ContextBundle, TaskType, ToolResult


class AgentTool(ABC):
    """
    Contrato común para todas las herramientas del agente.
    Cada herramienta declara qué tipos de tarea puede manejar
    y expone un método execute() estandarizado.
    """

    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool:
        """Devuelve True si esta herramienta puede procesar la tarea dada."""
        ...

    @abstractmethod
    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        """Ejecuta la tarea y devuelve el resultado."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__
