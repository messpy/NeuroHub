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

class HuggingFaceConfig(LLMProviderConfig):
    def __init__(self, api_key: str = None, debug_logger: DebugLogger = None):
        super().__init__('huggingface')
        self.debug_logger = debug_logger or DebugLogger(False)
        self.token = api_key or os.getenv('HF_TOKEN', '')
        self.base_url = (os.getenv('HF_HOST') or 'https://router.huggingface.co/v1').rstrip('/')
        self.default_model = 'openai/gpt-oss-20b:groq'
        self.current_model = self.get_model_from_config(self.default_model)
        self._available_models = None

    def get_api_url(self) -> str:
        return f'{self.base_url}/chat/completions'

    def is_configured(self) -> bool:
        return bool(self.token)

    def get_headers(self) -> Dict[str, str]:
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}

    def list_available_models(self) -> List[str]:
        if self._available_models is not None:
            return self._available_models

        try:
            list_url = f'{self.base_url}/models'
            r = requests.get(list_url, headers=self.get_headers(), timeout=10)
            if r.status_code == 200:
                data = r.json()
                models = [m.get('id', '') for m in data.get('data', []) if m.get('id')]
                self._available_models = models
                return models
        except Exception as e:
            self.debug_logger.dbg('Failed to list models:', str(e))
        return ['openai/gpt-oss-20b:groq', 'meta-llama/Llama-3.3-70B-Instruct:nvidia']

    def test_connection(self) -> bool:
        if not self.is_configured():
            print('ERROR: HF_TOKEN not set')
            return False
        try:
            payload = {
                'model': self.current_model,
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10
            }
            url = self.get_api_url()
            r = requests.post(url, json=payload, headers=self.get_headers(), timeout=30)
            if r.status_code == 200:
                print(f'OK: HuggingFace Router API (model: {self.current_model})')
                return True
            elif r.status_code == 404 or r.status_code == 400:
                print(f'ERROR: Model {self.current_model} not found, fetching available models...')
                available = self.list_available_models()
                if available:
                    self.current_model = available[0]
                    print(f'Switched to available model: {self.current_model}')
                    return self.test_connection()
                print('ERROR: No available models found')
                return False
            else:
                print(f'ERROR: HTTP {r.status_code}: {r.text[:200]}')
                return False
        except Exception as e:
            print(f'ERROR: {e}')
            return False

    def infer(self, prompt: str, opts: Dict[str, Any] = None) -> LLMResponse:
        start = time.time()
        try:
            messages = [{'role': 'user', 'content': prompt}]
            payload = {'model': self.current_model, 'messages': messages}

            if opts:
                if 'temperature' in opts:
                    payload['temperature'] = float(opts['temperature'])
                if 'top_p' in opts:
                    payload['top_p'] = float(opts['top_p'])
                if 'max_tokens' in opts:
                    payload['max_tokens'] = int(opts['max_tokens'])

            url = self.get_api_url()
            r = requests.post(url, json=payload, headers=self.get_headers(), timeout=120)
            elapsed = time.time() - start

            if r.status_code == 404 or r.status_code == 400:
                available = self.list_available_models()
                if available and self.current_model not in available:
                    self.current_model = available[0]
                    return self.infer(prompt, opts)

            if r.status_code != 200:
                return create_llm_response(r.status_code, 'huggingface', self.current_model, '', f'HTTP {r.status_code}', elapsed)

            data = r.json()
            content = ''
            try:
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            except:
                pass
            if not content:
                content = json.dumps(data, ensure_ascii=False)

            usage = data.get('usage', {})
            return create_llm_response(200, 'huggingface', self.current_model, content, None, elapsed,
                                     usage.get('total_tokens'), usage.get('prompt_tokens'), usage.get('completion_tokens'))
        except Exception as e:
            return create_llm_response(500, 'huggingface', self.current_model, '', str(e), time.time() - start)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('prompt', nargs='*')
    p.add_argument('--test', action='store_true')
    p.add_argument('--list-models', action='store_true')
    p.add_argument('--model', type=str)
    args = p.parse_args()

    cfg = HuggingFaceConfig()
    if args.model:
        cfg.current_model = args.model

    if not cfg.is_configured():
        print('ERROR: HF_TOKEN not set', file=sys.stderr)
        return 2

    if args.list_models:
        models = cfg.list_available_models()
        print('Available HuggingFace models:')
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
