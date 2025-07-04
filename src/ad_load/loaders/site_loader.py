import yaml
from importlib import resources
from functools import lru_cache

@lru_cache
def load_site() -> dict[str, dict]:
    data = resources.files("ad_load.loaders").joinpath("sites.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(data)