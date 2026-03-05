"""
Interfaz de usuario en modo CLI.
Gestiona el loop de conversación y presenta los resultados al usuario.
"""

from __future__ import annotations

import sys
from typing import Optional

from ..models import AgentResponse, UserRequest
from ..orchestrator.agent_orchestrator import AgentOrchestrator


BANNER = """
╔══════════════════════════════════════════════════════╗
║           Agente IA de Programacion                  ║
║  Escribe tu tarea o pregunta. 'salir' para terminar. ║
╚══════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Comandos especiales:
  /ayuda          - Muestra este mensaje
  /memoria        - Muestra las reglas del proyecto guardadas
  /regla <texto>  - Añade una regla permanente al proyecto
  /borrar         - Limpia el historial de conversación
  salir / exit    - Termina la sesión
"""


class ChatSessionUI:
    """
    Loop principal de la sesión de chat en la terminal.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        active_file: Optional[str] = None,
    ):
        self._orchestrator = orchestrator
        self._active_file = active_file

    def start(self) -> None:
        print(BANNER)

        while True:
            try:
                user_input = input("Tu> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSesión terminada.")
                break

            if not user_input:
                continue

            if user_input.lower() in {"salir", "exit", "quit"}:
                print("Hasta luego.")
                break

            if user_input.lower() == "/ayuda":
                print(HELP_TEXT)
                continue

            if user_input.lower() == "/memoria":
                self._show_project_memory()
                continue

            if user_input.lower().startswith("/regla "):
                rule_text = user_input[7:].strip()
                self._add_project_rule(rule_text)
                continue

            if user_input.lower() == "/borrar":
                self._orchestrator._conv_memory.clear()
                print("[Historial borrado]")
                continue

            request = UserRequest(
                text=user_input,
                source="cli",
                file_path=self._active_file,
            )

            print("\nAgente> Procesando...\n")
            response = self._orchestrator.handle_request(request)
            self._display_response(response)

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------

    def _display_response(self, response: AgentResponse) -> None:
        status_icon = "OK" if response.success else "ERROR"
        print(f"[{status_icon}] {response.message}")

        if response.suggested_edits:
            print("\n--- Cambios propuestos ---")
            for patch in response.suggested_edits:
                print(f"\nArchivo: {patch.file_path}")
                if patch.explanation:
                    print(f"Nota: {patch.explanation}")
                print("```")
                print(patch.new_content[:1500])
                if len(patch.new_content) > 1500:
                    print(f"... [{len(patch.new_content) - 1500} caracteres más]")
                print("```")

            choice = input("\n¿Aplicar cambios? [s/N]: ").strip().lower()
            if choice == "s":
                for patch in response.suggested_edits:
                    self._orchestrator._repo.apply_patch(patch)
                    print(f"  Aplicado: {patch.file_path}")

        print()

    # ------------------------------------------------------------------
    # Comandos de gestión
    # ------------------------------------------------------------------

    def _show_project_memory(self) -> None:
        notes = self._orchestrator._proj_memory.all_notes()
        if not notes:
            print("[Sin reglas guardadas]")
            return
        for note in notes:
            tags = f" [{', '.join(note.tags)}]" if note.tags else ""
            print(f"  {note.key}{tags}: {note.value}")

    def _add_project_rule(self, rule_text: str) -> None:
        key = f"rule_{len(self._orchestrator._proj_memory.all_notes()) + 1}"
        self._orchestrator._proj_memory.set(key, rule_text, tags=["rule"])
        print(f"[Regla guardada: {key}]")
