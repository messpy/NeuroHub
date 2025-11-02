#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'services' / 'llm'))

from services.ai.provider_gemini import GeminiConfig
from services.ai.llm_common import DebugLogger

@pytest.fixture
def gemini_config():
    return GeminiConfig(debug_logger=DebugLogger(True, 2))

def test_gemini_init(gemini_config):
    assert gemini_config.default_model == 'gemini-2.5-flash'
    assert gemini_config.base_url.startswith('https://')

def test_gemini_is_configured(gemini_config):
    assert gemini_config.is_configured() == True

def test_gemini_list_models():
    cfg = GeminiConfig()
    if not cfg.is_configured():
        pytest.skip('GEMINI_API_KEY not set')
    models = cfg.list_available_models()
    assert len(models) > 0
    assert any('gemini' in m.lower() for m in models)

def test_gemini_connection():
    cfg = GeminiConfig()
    if not cfg.is_configured():
        pytest.skip('GEMINI_API_KEY not set')
    assert cfg.test_connection() == True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
