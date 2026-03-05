"""Tests para los modelos de datos."""

import pytest
from agente_ia.models import (
    AgentTask,
    CodeFile,
    CodePatch,
    ContextBundle,
    TaskStatus,
    TaskType,
    ToolResult,
    UserRequest,
    ValidationReport,
)


def test_user_request_defaults():
    req = UserRequest(text="Genera una función")
    assert req.source == "cli"
    assert req.file_path is None
    assert req.session_id  # debe tener un UUID


def test_agent_task_defaults():
    task = AgentTask(tipo=TaskType.GENERATE_CODE, descripcion="Prueba")
    assert task.estado == TaskStatus.PENDING
    assert task.id  # UUID generado


def test_code_patch():
    patch = CodePatch(file_path="src/main.py", new_content="print('hola')")
    assert patch.file_path == "src/main.py"
    assert "hola" in patch.new_content


def test_tool_result_with_validation():
    report = ValidationReport(passed=True, output="All tests passed")
    result = ToolResult(success=True, output="OK", validation=report)
    assert result.validation.passed


def test_context_bundle_defaults():
    bundle = ContextBundle()
    assert bundle.files == []
    assert bundle.project_rules == []
    assert bundle.recent_conversation_summary == ""
