import tempfile
from pathlib import Path
import pytest

import ad_load.loaders.script_loader as sl

def test_load_script_reads_file(tmp_path, monkeypatch):
    fake_dir = tmp_path / "injected_scripts"
    fake_dir.mkdir()
    test_file = fake_dir / "test_script.js"
    test_content = "console.log('Hello, World!');"
    test_file.write_text(test_content, encoding="utf-8")
    
    monkeypatch.setattr(sl, "_BASE_DIR", fake_dir)
    
    res = sl.load_script("test_script.js")
    
    assert res == test_content
    
def test_load_script_raises_if_missing(tmp_path, monkeypatch):
    empty_dir = tmp_path / "injected_scripts"
    empty_dir.mkdir()
    monkeypatch.setattr(sl, "_BASE_DIR", empty_dir)

    with pytest.raises(FileNotFoundError) as excinfo:
        sl.load_script("does_not_exist.js")
    assert "does_not_exist.js" in str(excinfo.value)
    assert str(empty_dir / "does_not_exist.js") in str(excinfo.value)
    