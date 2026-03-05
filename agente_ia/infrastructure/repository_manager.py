"""
Gestión del repositorio de código fuente.
Permite leer archivos del proyecto, aplicar patches y (opcionalmente) interactuar con git.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from ..models import CodeFile, CodePatch


IGNORED_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rs", ".rb", ".c", ".cpp", ".h", ".cs"}


class RepositoryManager:
    """
    Gestiona el acceso al repositorio local.
    """

    def __init__(self, root_path: str = "."):
        self._root = Path(root_path).resolve()

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def load_repo(self) -> list[CodeFile]:
        """Carga todos los archivos de código del repositorio."""
        files: list[CodeFile] = []
        for path in self._root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.suffix not in CODE_EXTENSIONS:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                lang = self._detect_language(path.suffix)
                files.append(CodeFile(path=str(path.relative_to(self._root)), content=content, language=lang))
            except Exception:
                continue
        return files

    def read_file(self, relative_path: str) -> Optional[CodeFile]:
        full_path = self._root / relative_path
        if not full_path.exists():
            return None
        content = full_path.read_text(encoding="utf-8", errors="ignore")
        lang = self._detect_language(full_path.suffix)
        return CodeFile(path=relative_path, content=content, language=lang)

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    def apply_patch(self, patch: CodePatch) -> bool:
        """Aplica un CodePatch escribiendo el nuevo contenido al archivo."""
        target = self._root / patch.file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(patch.new_content, encoding="utf-8")
        return True

    def apply_patches(self, patches: list[CodePatch]) -> list[str]:
        """Aplica una lista de patches y devuelve rutas de los archivos modificados."""
        modified: list[str] = []
        for patch in patches:
            if self.apply_patch(patch):
                modified.append(patch.file_path)
        return modified

    # ------------------------------------------------------------------
    # Git helpers (opcionales)
    # ------------------------------------------------------------------

    def git_status(self) -> str:
        return self._run_git("status", "--short")

    def create_branch(self, name: str) -> bool:
        result = self._run_git("checkout", "-b", name)
        return "error" not in result.lower()

    def git_diff(self, file_path: Optional[str] = None) -> str:
        args = ["diff"]
        if file_path:
            args.append(file_path)
        return self._run_git(*args)

    def git_commit(self, message: str, files: Optional[list[str]] = None) -> bool:
        if files:
            for f in files:
                self._run_git("add", f)
        else:
            self._run_git("add", "-A")
        result = self._run_git("commit", "-m", message)
        return "error" not in result.lower()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _run_git(self, *args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(self._root),
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"error: {e}"

    @staticmethod
    def _detect_language(suffix: str) -> str:
        mapping = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".java": "java", ".go": "go", ".rs": "rust",
            ".rb": "ruby", ".c": "c", ".cpp": "cpp", ".h": "c",
            ".cs": "csharp",
        }
        return mapping.get(suffix.lower(), "text")
