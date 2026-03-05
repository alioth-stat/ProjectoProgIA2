"""
Modelos de datos centrales del agente IA de programación.
Todos los módulos se comunican mediante estos tipos bien definidos.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enumeraciones
# ---------------------------------------------------------------------------

class TaskType(str, Enum):
    EXPLAIN_CODE = "explain_code"
    GENERATE_CODE = "generate_code"
    REFACTOR_CODE = "refactor_code"
    WRITE_TESTS = "write_tests"
    RUN_TESTS = "run_tests"
    STATIC_ANALYSIS = "static_analysis"
    GENERATE_DOCS = "generate_docs"
    EXPLORE_CODEBASE = "explore_codebase"
    APPLY_PATCH = "apply_patch"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Request / Response de cara al usuario
# ---------------------------------------------------------------------------

@dataclass
class UserRequest:
    """Solicitud proveniente del usuario a través de la UI."""
    text: str
    source: str = "cli"                  # "cli" | "ide" | "web"
    file_path: Optional[str] = None      # archivo activo en el editor
    selection_range: Optional[tuple[int, int]] = None  # (línea_inicio, línea_fin)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AgentResponse:
    """Respuesta del agente hacia la UI."""
    message: str
    suggested_edits: list[CodePatch] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    task_results: list[ToolResult] = field(default_factory=list)
    success: bool = True


# ---------------------------------------------------------------------------
# Tarea interna del agente
# ---------------------------------------------------------------------------

@dataclass
class AgentTask:
    """Unidad de trabajo que el orquestador despacha a un AgentTool."""
    tipo: TaskType
    descripcion: str
    input_context: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estado: TaskStatus = TaskStatus.PENDING
    resultado: Optional[ToolResult] = None


# ---------------------------------------------------------------------------
# Contexto para el LLM
# ---------------------------------------------------------------------------

@dataclass
class CodeFile:
    """Representación de un archivo de código en memoria."""
    path: str
    content: str
    language: str = "python"
    symbols: list[str] = field(default_factory=list)  # funciones, clases, etc.


@dataclass
class ContextBundle:
    """Paquete de contexto que se pasa al LLM junto con la instrucción."""
    files: list[CodeFile] = field(default_factory=list)
    project_rules: list[str] = field(default_factory=list)
    recent_conversation_summary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resultados de herramientas
# ---------------------------------------------------------------------------

@dataclass
class CodePatch:
    """Cambio propuesto sobre un archivo."""
    file_path: str
    new_content: str
    diff: str = ""
    explanation: str = ""


@dataclass
class ValidationReport:
    """Resultado de tests o análisis estático."""
    passed: bool
    output: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Resultado genérico devuelto por cualquier AgentTool."""
    success: bool
    output: str
    patches: list[CodePatch] = field(default_factory=list)
    validation: Optional[ValidationReport] = None
    metadata: dict[str, Any] = field(default_factory=dict)
