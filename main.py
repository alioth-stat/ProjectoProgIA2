"""
Punto de entrada principal del Agente IA de Programación.

Uso:
    python main.py                          # Modo interactivo en el directorio actual
    python main.py --project /ruta/proyecto # Apuntar a otro proyecto
    python main.py --file src/app.py        # Archivo activo inicial
    python main.py --auto-apply             # Aplica patches automáticamente
    python main.py --no-telemetry           # Desactiva logs de telemetría
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agente IA de Programación - Asistente inteligente para tu código",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--project", "-p",
        default=".",
        help="Ruta raíz del proyecto a analizar (por defecto: directorio actual)",
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Archivo activo inicial (contexto preferente para el agente)",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        default=False,
        help="Aplica los patches generados automáticamente sin confirmación",
    )
    parser.add_argument(
        "--no-telemetry",
        action="store_true",
        default=False,
        help="Desactiva el registro de telemetría",
    )
    parser.add_argument(
        "--memory-dir",
        default=".agente_ia",
        help="Directorio donde se guarda la memoria del agente (por defecto: .agente_ia)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    project_root = str(Path(args.project).resolve())
    if not Path(project_root).exists():
        print(f"Error: El directorio del proyecto '{project_root}' no existe.", file=sys.stderr)
        sys.exit(1)

    # Importación tardía para que los errores de configuración sean informativos
    from agente_ia.factory import build_agent

    _, ui = build_agent(
        project_root=project_root,
        memory_dir=args.memory_dir,
        active_file=args.file,
        auto_apply_patches=args.auto_apply,
        telemetry_enabled=not args.no_telemetry,
    )

    ui.start()


if __name__ == "__main__":
    main()
