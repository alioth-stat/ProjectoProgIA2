"""Tests para la capa de infraestructura."""

import json
import os
import tempfile

import pytest

from agente_ia.infrastructure.llm_client import LLMClient, MockLLMProvider
from agente_ia.infrastructure.memory_store import ConversationMemoryStore, ProjectMemoryStore
from agente_ia.infrastructure.telemetry_logger import TelemetryLogger


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

def test_mock_provider_returns_fixed_response():
    provider = MockLLMProvider(fixed_response="def hola(): pass")
    client = LLMClient(provider=provider)
    result = client.complete("eres un asistente", "genera una función")
    assert result == "def hola(): pass"


def test_llm_client_from_env_uses_mock_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient.from_env()
    response = client.complete("system", "user")
    assert isinstance(response, str)


# ---------------------------------------------------------------------------
# ConversationMemoryStore
# ---------------------------------------------------------------------------

def test_conversation_memory_add_and_retrieve():
    store = ConversationMemoryStore()
    store.add_turn("user", "Hola agente")
    store.add_turn("agent", "Hola usuario")
    history = store.get_history()
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].content == "Hola usuario"


def test_conversation_memory_summarize():
    store = ConversationMemoryStore()
    store.add_turn("user", "Pregunta larga sobre código")
    summary = store.summarize()
    assert "USER" in summary


def test_conversation_memory_persistence():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        store = ConversationMemoryStore(persist_path=path)
        store.add_turn("user", "Mensaje persistido")

        store2 = ConversationMemoryStore(persist_path=path)
        history = store2.get_history()
        assert len(history) == 1
        assert history[0].content == "Mensaje persistido"
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# ProjectMemoryStore
# ---------------------------------------------------------------------------

def test_project_memory_set_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ProjectMemoryStore(persist_path=f"{tmpdir}/mem.json")
        store.set("estilo", "Usa snake_case siempre", tags=["rule"])
        assert store.get("estilo") == "Usa snake_case siempre"


def test_project_memory_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ProjectMemoryStore(persist_path=f"{tmpdir}/mem.json")
        store.set("r1", "Regla 1", tags=["rule"])
        store.set("r2", "Regla 2", tags=["rule"])
        store.set("info", "Información sin regla", tags=["info"])
        rules = store.as_rules_text()
        assert len(rules) == 2
        assert "Regla 1" in rules


# ---------------------------------------------------------------------------
# TelemetryLogger
# ---------------------------------------------------------------------------

def test_telemetry_logger_writes_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(log_dir=tmpdir, enabled=True)
        logger.log_user_request("Hola", "cli")
        logger.log_agent_response("Respuesta del agente")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".jsonl")]
        assert len(log_files) == 1

        with open(os.path.join(tmpdir, log_files[0])) as f:
            lines = [json.loads(l) for l in f.readlines()]

        assert len(lines) == 2
        assert lines[0]["event"] == "user_request"
        assert lines[1]["event"] == "agent_response"


def test_telemetry_logger_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = TelemetryLogger(log_dir=tmpdir, enabled=False)
        logger.log_user_request("Test", "cli")
        log_files = os.listdir(tmpdir)
        assert len(log_files) == 0
