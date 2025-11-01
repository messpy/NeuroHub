from pathlib import Path
import yaml

CFG = Path("config/config.yaml")

def test_config_exists():
    assert CFG.exists(), "config/config.yaml がありません"

def test_config_parse_yaml():
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "llm" in data
