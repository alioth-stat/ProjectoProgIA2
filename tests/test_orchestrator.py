"""Tests de integración para el orquestador."""

import pytest

from agente_ia.infrastructure.llm_client import LLMClient, MockLLMProvider
from agente_ia.infrastructure.memory_store import ConversationMemoryStore, ProjectMemoryStore
from agente_ia.infrastructure.repository_manager import RepositoryManager
from agente_ia.infrastructure.telemetry_logger import TelemetryLogger
from agente_ia.models import CodeFile, TaskType, UserRequest
from agente_ia.orchestrator.agent_orchestrator import AgentOrchestrator
from agente_ia.orchestrator.intent_classifier import IntentClassifier
from agente_ia.tools.code_analyzer import CodeAnalyzer, CodebaseIndex
from agente_ia.tools.code_generation_tool import CodeGenerationTool
from agente_ia.tools.context_builder import ContextBuilder
from agente_ia.tools.doc_generator_tool import DocGeneratorTool


# ---------------------------------------------------------------------------
# IntentClassifier
# ---------------------------------------------------------------------------

def test_classify_generate():
    clf = IntentClassifier()
    assert clf.classify("genera una función de ordenación") == TaskType.GENERATE_CODE


def test_classify_explain():
    clf = IntentClassifier()
    assert clf.classify("explica cómo funciona este código") == TaskType.EXPLAIN_CODE


def test_classify_refactor():
    clf = IntentClassifier()
    assert clf.classify("refactoriza la clase User") == TaskType.REFACTOR_CODE


def test_classify_run_tests():
    clf = IntentClassifier()
    assert clf.classify("ejecuta los tests del proyecto") == TaskType.RUN_TESTS


def test_classify_static_analysis():
    clf = IntentClassifier()
    assert clf.classify("analiza el código con mypy") == TaskType.STATIC_ANALYSIS


def test_classify_default():
    clf = IntentClassifier()
    # Texto sin palabras clave claras → default GENERATE_CODE
    assert clf.classify("algo raro xyz") == TaskType.GENERATE_CODE


# ---------------------------------------------------------------------------
# AgentOrchestrator (integración con Mock LLM)
# ---------------------------------------------------------------------------

def _make_orchestrator(mock_response: str = "def f(): pass") -> AgentOrchestrator:
    llm = LLMClient(provider=MockLLMProvider(mock_response))
    index = CodebaseIndex(
        files=[CodeFile(path="app.py", content="# app principal", language="python")]
    )
    analyzer = CodeAnalyzer()
    analyzer._index = index
    builder = ContextBuilder(index=index)
    tools = [
        analyzer,
        CodeGenerationTool(llm=llm, context_builder=builder),
        DocGeneratorTool(llm=llm, context_builder=builder),
    ]
    return AgentOrchestrator(
        tools=tools,
        context_builder=builder,
        code_analyzer=analyzer,
        repo_manager=RepositoryManager("."),
        conversation_memory=ConversationMemoryStore(),
        project_memory=ProjectMemoryStore(persist_path="/tmp/test_pm.json"),
        logger=TelemetryLogger(enabled=False),
    )


def test_orchestrator_handle_generate_request():
    orch = _make_orchestrator("def nueva(): return 1")
    req = UserRequest(text="genera una función nueva")
    response = orch.handle_request(req)
    assert response.success
    assert len(response.suggested_edits) > 0


def test_orchestrator_handle_explain_request():
    orch = _make_orchestrator("Esta función hace X.")
    req = UserRequest(text="explica cómo funciona app.py", file_path="app.py")
    response = orch.handle_request(req)
    assert response.success
    assert "X" in response.message or len(response.message) > 0


def test_orchestrator_conversation_memory_updated():
    orch = _make_orchestrator()
    req = UserRequest(text="genera algo")
    orch.handle_request(req)
    history = orch._conv_memory.get_history()
    assert len(history) == 2  # un turno de user + uno de agent
    assert history[0].role == "user"
    assert history[1].role == "agent"


def test_orchestrator_plan_returns_task():
    orch = _make_orchestrator()
    req = UserRequest(text="refactoriza el módulo auth")
    tasks = orch.plan_tasks(req)
    assert len(tasks) >= 1
    assert tasks[0].tipo == TaskType.REFACTOR_CODE
