#!/usr/bin/env python3
import sys
from pathlib import Path
import yaml
import argparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / 'config' / 'llm_config.yaml'

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

def show_current():
    config = load_config()
    providers = config.get('llm', {}).get('providers', {})
    print('\n現在の設定:')
    for name, cfg in providers.items():
        if cfg.get('enabled'):
            print(f'  {name}: {cfg.get(\"model\")}')

def switch_to_ollama(model='qwen2.5:1.5b-instruct'):
    config = load_config()
    if 'llm' not in config:
        config['llm'] = {'providers': {}}
    
    for p in config['llm']['providers']:
        config['llm']['providers'][p]['enabled'] = False
    
    if 'ollama' not in config['llm']['providers']:
        config['llm']['providers']['ollama'] = {}
    
    config['llm']['providers']['ollama'].update({
        'enabled': True,
        'model': model,
        'api_url': 'http://localhost:11434',
        'max_tokens': 500,
        'temperature': 0.3,
        'timeout': 30,
        'priority': 1
    })
    
    save_config(config)
    print(f'\nOllamaに切り替えました: {model}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--show', action='store_true')
    parser.add_argument('--model', default='qwen2.5:1.5b-instruct')
    args = parser.parse_args()
    
    if args.show:
        show_current()
    else:
        switch_to_ollama(args.model)

if __name__ == '__main__':
    main()
