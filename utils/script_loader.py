from pathlib import Path
from functools import lru_cache

_BASE_DIR = Path(__file__).resolve().parent.parent / "injected_scripts"

@lru_cache
def load_script(script_name: str) -> str:
    path = _BASE_DIR / script_name
    if not path.exists():
        raise FileNotFoundError(f"Script {script_name} not found in {path}")
    return path.read_text(encoding="utf-8")