"""
Herramienta de análisis estático: ejecuta flake8 y mypy.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..models import AgentTask, ContextBundle, TaskType, ToolResult, ValidationReport
from .base_tool import AgentTool


class StaticAnalysisTool(AgentTool):
    """
    Ejecuta linters y verificadores de tipos sobre el proyecto o un archivo concreto.
    """

    HANDLED_TASKS = {TaskType.STATIC_ANALYSIS}

    def __init__(self, project_root: str = "."):
        self._root = Path(project_root).resolve()

    def can_handle(self, task: AgentTask) -> bool:
        return task.tipo in self.HANDLED_TASKS

    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        target: Optional[str] = task.input_context.get("file_path")
        run_mypy: bool = task.input_context.get("run_mypy", True)
        return self.analyze(target=target, run_mypy=run_mypy)

    def analyze(
        self,
        target: Optional[str] = None,
        run_mypy: bool = True,
    ) -> ToolResult:
        path_arg = target or "."
        all_output: list[str] = []
        all_errors: list[str] = []
        all_warnings: list[str] = []

        # Flake8
        flake8_result = self._run_tool(
            [sys.executable, "-m", "flake8", "--max-line-length=120", path_arg]
        )
        if flake8_result:
            all_output.append(f"=== flake8 ===\n{flake8_result}")
            for line in flake8_result.splitlines():
                if " E" in line or " F" in line:
                    all_errors.append(line.strip())
                elif " W" in line:
                    all_warnings.append(line.strip())

        # mypy (opcional)
        if run_mypy:
            mypy_result = self._run_tool(
                [sys.executable, "-m", "mypy", "--ignore-missing-imports", path_arg]
            )
            if mypy_result:
                all_output.append(f"=== mypy ===\n{mypy_result}")
                for line in mypy_result.splitlines():
                    if "error:" in line:
                        all_errors.append(line.strip())
                    elif "note:" in line or "warning:" in line:
                        all_warnings.append(line.strip())

        passed = len(all_errors) == 0
        full_output = "\n\n".join(all_output) if all_output else "Sin problemas detectados."
        report = ValidationReport(
            passed=passed,
            output=full_output,
            errors=all_errors,
            warnings=all_warnings,
        )
        summary = (
            f"Análisis estático {'OK' if passed else 'con problemas'}. "
            f"{len(all_errors)} errores, {len(all_warnings)} advertencias."
        )
        return ToolResult(success=passed, output=summary, validation=report)

    def _run_tool(self, cmd: list[str]) -> str:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self._root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            return (result.stdout + result.stderr).strip()
        except FileNotFoundError:
            return ""
        except Exception as e:
            return f"Error: {e}"
