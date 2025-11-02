#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path
from typing import Dict, Any, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from .llm_common import load_env_from_config, DebugLogger, LLMProviderConfig, LLMResponse, create_llm_response
except ImportError:
    from llm_common import load_env_from_config, DebugLogger, LLMProviderConfig, LLMResponse, create_llm_response

load_env_from_config()

try:
    import requests
except ImportError:
    print('[error] requests not installed', file=sys.stderr)
    sys.exit(1)

class GeminiConfig(LLMProviderConfig):
    def __init__(self, api_key: str = None, debug_logger: DebugLogger = None):
        super().__init__('gemini')
        self.debug_logger = debug_logger or DebugLogger(False)
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        self.base_url = os.getenv('GEMINI_API_URL', 'https://generativelanguage.googleapis.com/v1').rstrip('/')
        self.default_model = 'gemini-2.5-flash'
        self.current_model = self.get_model_from_config(self.default_model)
        self._available_models = None

    def get_api_url(self, model: str = None) -> str:
        return f'{self.base_url}/models/{model or self.current_model}:generateContent?key={self.api_key}'

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def list_available_models(self) -> List[str]:
        if self._available_models is not None:
            return self._available_models

        try:
            list_url = f'{self.base_url}/models?key={self.api_key}'
            r = requests.get(list_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                models = []
                for model in data.get('models', []):
                    name = model.get('name', '').replace('models/', '')
                    supported_methods = model.get('supportedGenerationMethods', [])
                    if 'generateContent' in supported_methods:
                        models.append(name)
                self._available_models = models
                return models
        except Exception as e:
            self.debug_logger.dbg('Failed to list models:', str(e))
        return []

    def test_connection(self) -> bool:
        if not self.is_configured():
            print('ERROR: GEMINI_API_KEY not set')
            return False
        try:
            payload = {'contents': [{'parts': [{'text': 'Hello'}]}]}
            url = self.get_api_url()
            r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=10)
            if r.status_code == 200:
                print(f'OK: Gemini API (model: {self.current_model})')
                return True
            elif r.status_code == 404:
                print(f'ERROR: Model {self.current_model} not found, fetching available models...')
                available = self.list_available_models()
                if available:
                    self.current_model = available[0]
                    print(f'Switched to available model: {self.current_model}')
                    return self.test_connection()
                print('ERROR: No available models found')
                return False
            else:
                print(f'ERROR: HTTP {r.status_code}')
                return False
        except Exception as e:
            print(f'ERROR: {e}')
            return False

    def infer(self, prompt: str, opts: Dict[str, Any] = None) -> LLMResponse:
        start = time.time()
        try:
            payload = {'contents': [{'parts': [{'text': prompt}]}]}
            if opts:
                gen_config = {}
                if 'temperature' in opts:
                    gen_config['temperature'] = float(opts['temperature'])
                if 'top_p' in opts:
                    gen_config['topP'] = float(opts['top_p'])
                if gen_config:
                    payload['generationConfig'] = gen_config

            url = self.get_api_url()
            r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
            elapsed = time.time() - start

            if r.status_code == 404:
                available = self.list_available_models()
                if available and self.current_model not in available:
                    self.current_model = available[0]
                    return self.infer(prompt, opts)

            if r.status_code != 200:
                return create_llm_response(r.status_code, 'gemini', self.current_model, '', f'HTTP {r.status_code}', elapsed)

            data = r.json()
            content = ''
            try:
                parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                for p in parts:
                    if isinstance(p, dict) and 'text' in p:
                        content = p['text'].strip()
                        break
            except:
                pass
            if not content:
                content = json.dumps(data, ensure_ascii=False)

            usage = data.get('usageMetadata', {})
            return create_llm_response(
                200, 'gemini', self.current_model, content, None, elapsed,
                tokens_used=usage.get('totalTokenCount'),
                tokens_input=usage.get('promptTokenCount'),
                tokens_output=usage.get('candidatesTokenCount')
            )
        except Exception as e:
            return create_llm_response(500, 'gemini', self.current_model, '', str(e), time.time() - start)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('prompt', nargs='*')
    p.add_argument('--test', action='store_true')
    p.add_argument('--list-models', action='store_true')
    p.add_argument('--model', type=str)
    args = p.parse_args()

    cfg = GeminiConfig()
    if args.model:
        cfg.current_model = args.model

    if not cfg.is_configured():
        print('ERROR: GEMINI_API_KEY not set', file=sys.stderr)
        return 2

    if args.list_models:
        models = cfg.list_available_models()
        print('Available Gemini models:')
        for m in models:
            print(f'  - {m}')
        return 0

    if args.test:
        if cfg.test_connection():
            resp = cfg.infer('Say hello in Japanese')
            print(f'Response: {resp.content}')
        return 0

    if not args.prompt:
        print('ERROR: prompt required', file=sys.stderr)
        return 2

    resp = cfg.infer(' '.join(args.prompt))
    print(resp.content)
    return 0

if __name__ == '__main__':
    sys.exit(main())
