import time
from pathlib import Path
from functools import lru_cache

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

@lru_cache
def _load_raw_template(name: str) -> str:
    path = _TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template {name} not found in {path}")
    return path.read_text(encoding="utf-8")

def render_template(name: str, **kwargs) -> str:
    raw = _load_raw_template(name)
    ctx = {"timestamp": int(time.time()), **kwargs}
    return raw.format(**ctx)