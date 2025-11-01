#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/mnt/c/Users/kenny/sandbox/NeuroHub')
os.environ['PYTHONPATH'] = '/mnt/c/Users/kenny/sandbox/NeuroHub'
os.environ['OLLAMA_HOST'] = 'http://127.0.0.1:11434'

from services.llm.llm_common import DebugLogger
try:
    from services.llm import provider_ollama
    debug = DebugLogger(True)
    config = provider_ollama.OllamaConfig(debug_logger=debug)
    print('Testing Ollama connection...')
    result = config.test_connection()
    print(f'Connection test result: {result}')

    if result:
        print('Testing model availability...')
        model = config.ensure_model_available()
        print(f'Available model: {model}')

        print('Testing inference...')
        response = config.infer('Return exactly: PONG')
        print(f'Response: {response.content}')
        print(f'Status: {response.status_code}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
