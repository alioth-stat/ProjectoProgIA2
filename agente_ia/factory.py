"""
Factory: construye el agente completo con todas sus dependencias.
Punto central de configuración (dependency injection manual).
"""

from __future__ import annotations

import os
from typing import Optional

from .infrastructure.llm_client import LLMClient
from .infrastructure.memory_store import ConversationMemoryStore, ProjectMemoryStore
from .infrastructure.repository_manager import RepositoryManager
from .infrastructure.telemetry_logger import TelemetryLogger
from .orchestrator.agent_orchestrator import AgentOrchestrator
from .tools.code_analyzer import CodeAnalyzer, CodebaseIndex
from .tools.code_generation_tool import CodeGenerationTool
from .tools.context_builder import ContextBuilder
from .tools.doc_generator_tool import DocGeneratorTool
from .tools.static_analysis_tool import StaticAnalysisTool
from .tools.test_runner_tool import TestRunnerTool
from .ui.chat_session_ui import ChatSessionUI


def build_agent(
    project_root: str = ".",
    memory_dir: str = ".agente_ia",
    active_file: Optional[str] = None,
    auto_apply_patches: bool = False,
    telemetry_enabled: bool = True,
) -> tuple[AgentOrchestrator, ChatSessionUI]:
    """
    Construye y conecta todos los componentes del agente.

    Returns:
        (orquestador, interfaz_cli) listos para usar.
    """
    # 1. Infraestructura
    logger = TelemetryLogger(log_dir=f"{memory_dir}/logs", enabled=telemetry_enabled)
    llm = LLMClient.from_env(logger=logger)
    conv_memory = ConversationMemoryStore(persist_path=f"{memory_dir}/conversation.json")
    proj_memory = ProjectMemoryStore(persist_path=f"{memory_dir}/project_memory.json")
    repo = RepositoryManager(root_path=project_root)

    # 2. Indexar el codebase
    analyzer = CodeAnalyzer()
    print(f"Indexando proyecto en '{project_root}'...")
    files = repo.load_repo()
    index = analyzer.build_index(files)
    print(index.summary())

    # 3. Context builder con reglas del proyecto
    rules = proj_memory.as_rules_text()
    ctx_builder = ContextBuilder(index=index, project_rules=rules)

    # 4. Herramientas
    tools = [
        analyzer,
        CodeGenerationTool(llm=llm, context_builder=ctx_builder),
        DocGeneratorTool(llm=llm, context_builder=ctx_builder),
        TestRunnerTool(project_root=project_root),
        StaticAnalysisTool(project_root=project_root),
    ]

    # 5. Orquestador
    orchestrator = AgentOrchestrator(
        tools=tools,
        context_builder=ctx_builder,
        code_analyzer=analyzer,
        repo_manager=repo,
        conversation_memory=conv_memory,
        project_memory=proj_memory,
        logger=logger,
        auto_apply_patches=auto_apply_patches,
    )

    # 6. UI
    ui = ChatSessionUI(orchestrator=orchestrator, active_file=active_file)

    return orchestrator, ui
