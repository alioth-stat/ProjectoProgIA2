"""
Análisis del código fuente del proyecto.
CodebaseIndex: estructura de datos con los archivos y símbolos del proyecto.
CodeAnalyzer: herramienta que explora el codebase y produce un índice.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..models import AgentTask, CodeFile, ContextBundle, TaskType, ToolResult
from .base_tool import AgentTool


# ---------------------------------------------------------------------------
# Índice del codebase
# ---------------------------------------------------------------------------

@dataclass
class SymbolInfo:
    name: str
    kind: str          # "function" | "class" | "method" | "variable"
    file_path: str
    line: int
    docstring: str = ""


@dataclass
class CodebaseIndex:
    """Mapa de archivos y símbolos del proyecto."""
    files: list[CodeFile] = field(default_factory=list)
    symbols: list[SymbolInfo] = field(default_factory=list)

    def find_file(self, path: str) -> Optional[CodeFile]:
        for f in self.files:
            if f.path == path or f.path.endswith(path):
                return f
        return None

    def find_symbol(self, name: str) -> list[SymbolInfo]:
        name_lower = name.lower()
        return [s for s in self.symbols if name_lower in s.name.lower()]

    def files_by_language(self, language: str) -> list[CodeFile]:
        return [f for f in self.files if f.language == language]

    def summary(self) -> str:
        langs: dict[str, int] = {}
        for f in self.files:
            langs[f.language] = langs.get(f.language, 0) + 1
        lang_str = ", ".join(f"{v} {k}" for k, v in langs.items())
        return (
            f"Proyecto con {len(self.files)} archivos ({lang_str}) "
            f"y {len(self.symbols)} símbolos indexados."
        )


# ---------------------------------------------------------------------------
# Extractor de símbolos Python (via AST)
# ---------------------------------------------------------------------------

def _extract_python_symbols(code_file: CodeFile) -> list[SymbolInfo]:
    symbols: list[SymbolInfo] = []
    try:
        tree = ast.parse(code_file.content)
    except SyntaxError:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            symbols.append(SymbolInfo(
                name=node.name,
                kind="function",
                file_path=code_file.path,
                line=node.lineno,
                docstring=doc,
            ))
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            symbols.append(SymbolInfo(
                name=node.name,
                kind="class",
                file_path=code_file.path,
                line=node.lineno,
                docstring=doc,
            ))
            # Métodos de la clase
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mdoc = ast.get_docstring(item) or ""
                    symbols.append(SymbolInfo(
                        name=f"{node.name}.{item.name}",
                        kind="method",
                        file_path=code_file.path,
                        line=item.lineno,
                        docstring=mdoc,
                    ))
    return symbols


# ---------------------------------------------------------------------------
# Herramienta de análisis
# ---------------------------------------------------------------------------

class CodeAnalyzer(AgentTool):
    """
    Indexa el codebase y puede responder consultas sobre su estructura.
    """

    HANDLED_TASKS = {TaskType.EXPLORE_CODEBASE}

    def __init__(self, index: Optional[CodebaseIndex] = None):
        self._index = index or CodebaseIndex()

    # ------------------------------------------------------------------
    # Construcción del índice
    # ------------------------------------------------------------------

    def build_index(self, files: list[CodeFile]) -> CodebaseIndex:
        """Construye un índice completo a partir de una lista de CodeFile."""
        self._index = CodebaseIndex(files=files)
        for cf in files:
            if cf.language == "python":
                self._index.symbols.extend(_extract_python_symbols(cf))
        return self._index

    @property
    def index(self) -> CodebaseIndex:
        return self._index

    # ------------------------------------------------------------------
    # AgentTool
    # ------------------------------------------------------------------

    def can_handle(self, task: AgentTask) -> bool:
        return task.tipo in self.HANDLED_TASKS

    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        query: str = task.input_context.get("query", "")
        results: list[str] = []

        if query:
            matches = self._index.find_symbol(query)
            if matches:
                results = [
                    f"{s.kind} '{s.name}' en {s.file_path}:{s.line}"
                    for s in matches[:10]
                ]
            else:
                results = [f"No se encontraron símbolos que coincidan con '{query}'."]
        else:
            results = [self._index.summary()]

        return ToolResult(success=True, output="\n".join(results))
