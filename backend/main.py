"""
FastAPI backend for the IA Programming Agent.
Exposes the agente_ia core as a REST API consumed by the React frontend.
Deploy this on Render.com (free tier) or any Python host.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Allow importing agente_ia from the parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agente_ia.infrastructure.llm_client import LLMClient
from agente_ia.infrastructure.memory_store import ConversationMemoryStore, ProjectMemoryStore
from agente_ia.infrastructure.repository_manager import RepositoryManager
from agente_ia.infrastructure.telemetry_logger import TelemetryLogger
from agente_ia.models import CodeFile, UserRequest
from agente_ia.orchestrator.agent_orchestrator import AgentOrchestrator
from agente_ia.tools.code_analyzer import CodeAnalyzer, CodebaseIndex
from agente_ia.tools.code_generation_tool import CodeGenerationTool
from agente_ia.tools.context_builder import ContextBuilder
from agente_ia.tools.doc_generator_tool import DocGeneratorTool
from agente_ia.tools.static_analysis_tool import StaticAnalysisTool
from agente_ia.tools.test_runner_tool import TestRunnerTool

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Agente IA de Programación API", version="0.1.0")

# CORS: allow the Netlify frontend (and localhost for dev)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory session store (one orchestrator per session_id)
# ---------------------------------------------------------------------------

_sessions: dict[str, AgentOrchestrator] = {}


def _build_orchestrator(session_id: str, code_snippets: list[dict]) -> AgentOrchestrator:
    """Creates a fresh orchestrator for a session with the provided code context."""
    logger = TelemetryLogger(log_dir=f"/tmp/agente_ia/{session_id}/logs", enabled=True)
    llm = LLMClient.from_env(logger=logger)

    # Build in-memory codebase from snippets provided by the user
    files = [
        CodeFile(
            path=s.get("filename", f"snippet_{i}.py"),
            content=s.get("content", ""),
            language=s.get("language", "python"),
        )
        for i, s in enumerate(code_snippets)
    ]

    analyzer = CodeAnalyzer()
    index = analyzer.build_index(files) if files else CodebaseIndex()

    conv_memory = ConversationMemoryStore(
        persist_path=f"/tmp/agente_ia/{session_id}/conversation.json"
    )
    proj_memory = ProjectMemoryStore(
        persist_path=f"/tmp/agente_ia/{session_id}/project_memory.json"
    )
    repo = RepositoryManager(root_path="/tmp")

    ctx_builder = ContextBuilder(index=index, project_rules=proj_memory.as_rules_text())

    tools = [
        analyzer,
        CodeGenerationTool(llm=llm, context_builder=ctx_builder),
        DocGeneratorTool(llm=llm, context_builder=ctx_builder),
        TestRunnerTool(project_root="/tmp"),
        StaticAnalysisTool(project_root="/tmp"),
    ]

    return AgentOrchestrator(
        tools=tools,
        context_builder=ctx_builder,
        code_analyzer=analyzer,
        repo_manager=repo,
        conversation_memory=conv_memory,
        project_memory=proj_memory,
        logger=logger,
        auto_apply_patches=False,
    )


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CodeSnippet(BaseModel):
    filename: str = "snippet.py"
    content: str
    language: str = "python"


class ChatRequest(BaseModel):
    session_id: str
    message: str
    code_snippets: list[CodeSnippet] = []
    active_file: Optional[str] = None


class PatchOut(BaseModel):
    file_path: str
    new_content: str
    explanation: str


class ChatResponse(BaseModel):
    message: str
    patches: list[PatchOut] = []
    success: bool


class SessionRequest(BaseModel):
    session_id: str
    code_snippets: list[CodeSnippet] = []


class SessionResponse(BaseModel):
    session_id: str
    files_indexed: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/session", response_model=SessionResponse)
def create_session(req: SessionRequest):
    """
    Initialise or refresh a session with a set of code snippets.
    Call this when the user loads files or pastes code.
    """
    snippets = [s.model_dump() for s in req.code_snippets]
    _sessions[req.session_id] = _build_orchestrator(req.session_id, snippets)
    return SessionResponse(
        session_id=req.session_id,
        files_indexed=len(req.code_snippets),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a message to the agent and receive a response."""
    # Auto-create session if it doesn't exist yet
    if req.session_id not in _sessions:
        snippets = [s.model_dump() for s in req.code_snippets]
        _sessions[req.session_id] = _build_orchestrator(req.session_id, snippets)
    elif req.code_snippets:
        # Refresh context if new snippets were sent
        snippets = [s.model_dump() for s in req.code_snippets]
        _sessions[req.session_id] = _build_orchestrator(req.session_id, snippets)

    orchestrator = _sessions[req.session_id]

    user_req = UserRequest(
        text=req.message,
        source="web",
        file_path=req.active_file,
    )

    try:
        response = orchestrator.handle_request(user_req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    patches = [
        PatchOut(
            file_path=p.file_path,
            new_content=p.new_content,
            explanation=p.explanation,
        )
        for p in response.suggested_edits
    ]

    return ChatResponse(
        message=response.message,
        patches=patches,
        success=response.success,
    )


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    """Clear a session and its memory."""
    _sessions.pop(session_id, None)
    return {"deleted": session_id}
