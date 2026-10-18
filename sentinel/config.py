import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}


def project_root() -> Path:
    import os
    env = os.environ.get("AST_PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


class Settings:
    def __init__(self):
        self.provider = os.environ.get("AST_PROVIDER", "openrouter").lower()
        self.model = os.environ.get("AST_MODEL", "openrouter/free")
        self.fallback_provider = os.environ.get("AST_FALLBACK_PROVIDER", "groq").lower()
        self.fallback_model = os.environ.get("AST_FALLBACK_MODEL", "")
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.max_iterations = int(os.environ.get("AST_MAX_ITER", "10"))
        self.timeout = int(os.environ.get("AST_TIMEOUT", "120"))
