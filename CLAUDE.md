# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI programming agent project. The repository currently contains an architecture planning document (`crea un modelo de implementacion completa para mi.md`) that outlines the intended design. No implementation code exists yet — this is a greenfield project.

The target stack is Python-based, with an optional web frontend (FastAPI/Flask) and potential VS Code extension integration.

## Intended Architecture

The system is designed as 4 layers:

1. **User Interface** — CLI, web app (FastAPI/Flask + frontend), or VS Code extension
2. **Agent Orchestrator** — receives user requests, decomposes them into tasks, dispatches to tools
3. **Capabilities Layer** — specialized tools: code analyzer, context builder, LLM code generator, test runner, doc generator
4. **Infrastructure** — LLM provider abstraction, memory/persistence (JSON/SQLite → vector DB), repository manager, telemetry

### Key data types
- `UserRequest` → `AgentOrchestrator` → `list[AgentTask]` → `AgentTool.execute()` → `ToolResult` → `AgentResponse` with `list[CodePatch]`
- Each `AgentTool` implements `can_handle(task)` and `execute(task, context)`
- `ContextBuilder` selects relevant code snippets to include in LLM prompts

### Incremental build plan
- **v0**: CLI + mock LLM + basic orchestrator (explain/generate tasks) + minimal code analyzer
- **v1**: `ContextBuilder`, `ConversationMemoryStore` (JSON), unit tests per module
- **v2**: VS Code `IDEAdapter`, `CodePatch` application, `TestRunnerTool` (pytest)
- **v3**: Refactor/migration tasks, richer project memory, git integration

## Development Commands

No build system exists yet. When implementing, the expected commands will be:

```bash
# Run the agent CLI
python -m tu_agente

# Run tests
pytest

# Static analysis
flake8 .
mypy .
```

These should be updated in this file once the project structure is established.
