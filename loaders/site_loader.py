import yaml
from pathlib import Path
from functools import lru_cache

@lru_cache
def load_site() -> dict[str, dict]:
    path = Path(__file__).parent.parent / "tests" / "test_sites.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))