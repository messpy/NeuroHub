#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'services' / 'llm'))

from services.ai.provider_huggingface import HuggingFaceConfig
from services.ai.llm_common import DebugLogger

@pytest.fixture
def hf_config():
    return HuggingFaceConfig(debug_logger=DebugLogger(True, 2))

def test_hf_init(hf_config):
    assert hf_config.default_model == 'openai/gpt-oss-20b:groq'
    assert hf_config.base_url.startswith('https://')

def test_hf_is_configured(hf_config):
    assert hf_config.is_configured() == True

def test_hf_list_models():
    cfg = HuggingFaceConfig()
    if not cfg.is_configured():
        pytest.skip('HF_TOKEN not set')
    models = cfg.list_available_models()
    assert len(models) > 0

def test_hf_connection():
    cfg = HuggingFaceConfig()
    if not cfg.is_configured():
        pytest.skip('HF_TOKEN not set')
    assert cfg.test_connection() == True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
