"""
Herramienta para ejecutar tests (pytest) y reportar resultados.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ..models import AgentTask, ContextBundle, TaskType, ToolResult, ValidationReport
from .base_tool import AgentTool


class TestRunnerTool(AgentTool):
    """
    Ejecuta la suite de tests del proyecto y devuelve un ValidationReport.
    """

    HANDLED_TASKS = {TaskType.RUN_TESTS, TaskType.WRITE_TESTS}

    def __init__(self, project_root: str = ".", test_command: Optional[list[str]] = None):
        self._root = Path(project_root).resolve()
        self._test_cmd = test_command or [sys.executable, "-m", "pytest", "--tb=short", "-q"]

    def can_handle(self, task: AgentTask) -> bool:
        return task.tipo in self.HANDLED_TASKS

    def execute(self, task: AgentTask, context: ContextBundle) -> ToolResult:
        if task.tipo == TaskType.WRITE_TESTS:
            return ToolResult(
                success=False,
                output="La escritura de tests requiere CodeGenerationTool. Usa TaskType.GENERATE_CODE con instrucción específica.",
            )
        return self.run_tests(
            test_path=task.input_context.get("test_path"),
            extra_args=task.input_context.get("extra_args", []),
        )

    def run_tests(
        self,
        test_path: Optional[str] = None,
        extra_args: Optional[list[str]] = None,
    ) -> ToolResult:
        cmd = list(self._test_cmd)
        if test_path:
            cmd.append(test_path)
        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self._root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            errors: list[str] = []
            warnings: list[str] = []
            for line in output.splitlines():
                if "FAILED" in line or "ERROR" in line:
                    errors.append(line.strip())
                elif "WARNING" in line or "warn" in line.lower():
                    warnings.append(line.strip())

            report = ValidationReport(
                passed=passed,
                output=output,
                errors=errors,
                warnings=warnings,
            )
            summary = f"Tests {'PASARON' if passed else 'FALLARON'}. {len(errors)} errores, {len(warnings)} advertencias."
            return ToolResult(success=passed, output=summary, validation=report)

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="Timeout: los tests tardaron más de 120 segundos.")
        except FileNotFoundError:
            return ToolResult(success=False, output="pytest no encontrado. Instala con: pip install pytest")
        except Exception as e:
            return ToolResult(success=False, output=f"Error ejecutando tests: {e}")


# Necesario para la anotación Optional dentro del módulo
from typing import Optional
