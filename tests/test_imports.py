import importlib
import pytest

@pytest.mark.smoke
@pytest.mark.parametrize("mod", [
    "services.agent.agent_cli",
    "services.agent.weather_agent",
    "services.agent.web_agent",
    "services.llm.llm_common",
    "services.llm.provider_huggingface",
    "services.llm.provider_gemini",
    "services.llm.provider_ollama",
    "tools.bs_core",
])
def test_module_imports(mod):
    importlib.import_module(mod)
