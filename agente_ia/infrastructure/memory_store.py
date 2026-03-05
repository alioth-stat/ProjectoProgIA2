"""
Persistencia de memoria para el agente.
- ConversationMemoryStore: historial de la sesión actual.
- ProjectMemoryStore: reglas, convenciones y notas del proyecto.
Implementación inicial en JSON/SQLite (ampliable a vector DB).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class ConversationTurn:
    role: str          # "user" | "agent"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ProjectNote:
    key: str
    value: str
    tags: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Historial de conversación
# ---------------------------------------------------------------------------

class ConversationMemoryStore:
    """
    Almacena el historial de la conversación actual en memoria y lo persiste
    opcionalmente en un archivo JSON.
    """

    def __init__(self, persist_path: Optional[str] = None, max_turns: int = 50):
        self._turns: list[ConversationTurn] = []
        self._max_turns = max_turns
        self._persist_path = Path(persist_path) if persist_path else None

        if self._persist_path and self._persist_path.exists():
            self._load()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add_turn(self, role: str, content: str) -> None:
        turn = ConversationTurn(role=role, content=content)
        self._turns.append(turn)
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns:]
        self._save()

    def get_history(self, last_n: Optional[int] = None) -> list[ConversationTurn]:
        turns = self._turns
        if last_n:
            turns = turns[-last_n:]
        return list(turns)

    def summarize(self, last_n: int = 10) -> str:
        """Devuelve un resumen textual de los últimos N turnos."""
        turns = self.get_history(last_n)
        if not turns:
            return ""
        lines = [f"{t.role.upper()}: {t.content[:200]}" for t in turns]
        return "\n".join(lines)

    def clear(self) -> None:
        self._turns = []
        self._save()

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persist_path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in self._turns], f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        with open(self._persist_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return
        data = json.loads(content)
        self._turns = [ConversationTurn(**d) for d in data]


# ---------------------------------------------------------------------------
# Memoria del proyecto
# ---------------------------------------------------------------------------

class ProjectMemoryStore:
    """
    Almacena notas, convenciones y preferencias del proyecto.
    Persiste en JSON; las notas se recuperan por clave o por etiqueta.
    """

    def __init__(self, persist_path: str = ".agente_ia/project_memory.json"):
        self._path = Path(persist_path)
        self._notes: dict[str, ProjectNote] = {}

        if self._path.exists():
            self._load()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set(self, key: str, value: str, tags: Optional[list[str]] = None) -> None:
        self._notes[key] = ProjectNote(key=key, value=value, tags=tags or [])
        self._save()

    def get(self, key: str) -> Optional[str]:
        note = self._notes.get(key)
        return note.value if note else None

    def get_by_tag(self, tag: str) -> list[ProjectNote]:
        return [n for n in self._notes.values() if tag in n.tags]

    def all_notes(self) -> list[ProjectNote]:
        return list(self._notes.values())

    def delete(self, key: str) -> None:
        self._notes.pop(key, None)
        self._save()

    def as_rules_text(self) -> list[str]:
        """Devuelve las notas con la etiqueta 'rule' como lista de strings."""
        return [n.value for n in self.get_by_tag("rule")]

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in self._notes.items()},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def _load(self) -> None:
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._notes = {k: ProjectNote(**v) for k, v in data.items()}
