"""
Logger de telemetría: registra prompts, respuestas y acciones del agente
en archivos JSON para facilitar el debugging y análisis.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .llm_client import LLMRequest, LLMResponse


class TelemetryLogger:
    """
    Registra eventos del agente en formato JSON Lines (.jsonl).
    Cada línea es un evento independiente con timestamp.
    """

    def __init__(self, log_dir: str = ".agente_ia/logs", enabled: bool = True):
        self._enabled = enabled
        self._log_dir = Path(log_dir)
        if self._enabled:
            self._log_dir.mkdir(parents=True, exist_ok=True)
        self._session_id: str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # ------------------------------------------------------------------
    # Métodos de log
    # ------------------------------------------------------------------

    def log_user_request(self, text: str, source: str = "cli") -> None:
        self._write("user_request", {"text": text, "source": source})

    def log_agent_response(self, message: str) -> None:
        self._write("agent_response", {"message": message[:500]})

    def log_task_dispatch(self, task_type: str, task_id: str) -> None:
        self._write("task_dispatch", {"task_type": task_type, "task_id": task_id})

    def log_task_result(self, task_id: str, success: bool, summary: str) -> None:
        self._write("task_result", {"task_id": task_id, "success": success, "summary": summary[:300]})

    def log_llm_request(self, request: Any) -> None:
        self._write("llm_request", {
            "system_prompt_length": len(getattr(request, "system_prompt", "")),
            "user_message_length": len(getattr(request, "user_message", "")),
        })

    def log_llm_response(self, response: Any) -> None:
        self._write("llm_response", {
            "model": getattr(response, "model", "unknown"),
            "usage": getattr(response, "usage", {}),
            "content_length": len(getattr(response, "content", "")),
        })

    def log_patch_applied(self, file_path: str) -> None:
        self._write("patch_applied", {"file_path": file_path})

    def log_error(self, error: str, context: str = "") -> None:
        self._write("error", {"error": error, "context": context})

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _write(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self._enabled:
            return
        record = {
            "ts": datetime.utcnow().isoformat(),
            "session": self._session_id,
            "event": event_type,
            **payload,
        }
        log_file = self._log_dir / f"session_{self._session_id}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
