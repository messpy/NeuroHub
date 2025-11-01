#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""LLMプロバイダー切り替えツール"""# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-

import sys

from pathlib import Path""""""

import yaml

import argparseLLMプロバイダー切り替えツールLLMプロバイダー切り替えツール



ROOT = Path(__file__).resolve().parents[1]簡単なコマンドでプロバイダーとモデルを変更できる簡単なコマンドでプロバイダーとモデルを変更できる

CONFIG_FILE = ROOT / "config" / "llm_config.yaml"

""""""

PROVIDERS = {

    "ollama": {import sysimport sys

        "name": "Ollama",

        "default_model": "qwen2.5:1.5b-instruct",import osimport os

        "api_url": "http://localhost:11434"

    },from pathlib import Pathfrom pathlib import Path

    "gemini": {

        "name": "Google Gemini",import yamlimport yaml

        "default_model": "gemini-2.5-flash"

    },import argparseimport argparse

    "huggingface": {

        "name": "HuggingFace",

        "default_model": "mistralai/Mistral-7B-Instruct-v0.2"

    }# プロジェクトルート# プロジェクトルート

}

ROOT = Path(__file__).resolve().parents[1]ROOT = Path(__file__).resolve().parents[1]

def load_config():

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:sys.path.insert(0, str(ROOT))sys.path.insert(0, str(ROOT))

        return yaml.safe_load(f)



def save_config(config):

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:CONFIG_FILE = ROOT / "config" / "llm_config.yaml"CONFIG_FILE = ROOT / "config" / "llm_config.yaml"

        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)



def show_current():

    config = load_config()

    llm_config = config.get("llm", {})

    providers = llm_config.get("providers", {})# 利用可能なプロバイダーとモデル# 利用可能なプロバイダーとモデル



    print("\n" + "="*60)PROVIDERS = {PROVIDERS = {

    print("現在のLLM設定")

    print("="*60)    "ollama": {    "ollama": {



    enabled_providers = []        "name": "Ollama (ローカル)",        "name": "Ollama (ローカル)",

    for provider_name, provider_config in providers.items():

        if provider_config.get("enabled", False):        "models": {        "models": {

            model = provider_config.get("model", "N/A")

            priority = provider_config.get("priority", "N/A")            "qwen2.5:0.5b": "Qwen2.5 0.5B (超軽量・高速)",            "qwen2.5:0.5b": "Qwen2.5 0.5B (超軽量・高速)",

            enabled_providers.append((priority, provider_name, model))

                "qwen2.5:1.5b": "Qwen2.5 1.5B (軽量・推奨)",            "qwen2.5:1.5b": "Qwen2.5 1.5B (軽量・推奨)",

    if enabled_providers:

        enabled_providers.sort(key=lambda x: x[0])            "qwen2.5:3b": "Qwen2.5 3B (中性能)",            "qwen2.5:3b": "Qwen2.5 3B (中性能)",

        print("\n有効なプロバイダー:")

        for priority, name, model in enabled_providers:            "llama3": "Llama3 (高性能)",            "llama3": "Llama3 (高性能)",

            print(f"  {priority}. {name:12} - {model}")

    else:            "mistral": "Mistral (高性能)",            "mistral": "Mistral (高性能)",

        print("\n有効なプロバイダーがありません")

            },        },

    print("="*60 + "\n")

        "default_model": "qwen2.5:1.5b-instruct",        "default_model": "qwen2.5:1.5b-instruct",

def show_available():

    print("\n" + "="*60)        "api_url": "http://localhost:11434"        "api_url": "http://localhost:11434"

    print("利用可能なプロバイダー")

    print("="*60)    },    },



    for provider_id, info in PROVIDERS.items():    "gemini": {    "gemini": {

        print(f"\n{provider_id} - {info['name']}")

        print(f"  デフォルトモデル: {info['default_model']}")        "name": "Google Gemini",        "name": "Google Gemini",



    print("\n" + "="*60 + "\n")        "models": {        "models": {



def switch_provider(provider_name, model=None):            "gemini-2.5-flash": "Gemini 2.5 Flash (高速)",            "gemini-2.5-flash": "Gemini 2.5 Flash (高速)",

    if provider_name not in PROVIDERS:

        print(f"不明なプロバイダー: {provider_name}")            "gemini-pro": "Gemini Pro (標準)",            "gemini-pro": "Gemini Pro (標準)",

        print(f"利用可能: {', '.join(PROVIDERS.keys())}")

        sys.exit(1)            "gemini-1.5-pro": "Gemini 1.5 Pro (高性能)",            "gemini-1.5-pro": "Gemini 1.5 Pro (高性能)",



    provider_info = PROVIDERS[provider_name]        },        },

    if model is None:

        model = provider_info['default_model']        "default_model": "gemini-2.5-flash",        "default_model": "gemini-2.5-flash",



    config = load_config()        "note": "環境変数 GEMINI_API_KEY が必要"        "note": "環境変数 GEMINI_API_KEY が必要"



    if "llm" not in config:    },    },

        config["llm"] = {"providers": {}, "default_settings": {}}

        "huggingface": {    "huggingface": {

    if provider_name not in config["llm"]["providers"]:

        config["llm"]["providers"][provider_name] = {}        "name": "HuggingFace",        "name": "HuggingFace",



    # 全プロバイダーを無効化        "models": {        "models": {

    for p in config["llm"]["providers"]:

        config["llm"]["providers"][p]["enabled"] = False            "mistralai/Mistral-7B-Instruct-v0.2": "Mistral 7B",            "mistralai/Mistral-7B-Instruct-v0.2": "Mistral 7B",



    # 選択したプロバイダーを有効化            "meta-llama/Llama-2-7b-chat-hf": "Llama 2 7B",            "meta-llama/Llama-2-7b-chat-hf": "Llama 2 7B",

    config["llm"]["providers"][provider_name]["enabled"] = True

    config["llm"]["providers"][provider_name]["model"] = model        },        },

    config["llm"]["providers"][provider_name]["priority"] = 1

            "default_model": "mistralai/Mistral-7B-Instruct-v0.2",        "default_model": "mistralai/Mistral-7B-Instruct-v0.2",

    if provider_name == "ollama":

        config["llm"]["providers"][provider_name]["api_url"] = provider_info["api_url"]        "note": "環境変数 HUGGINGFACE_API_KEY が必要"        "note": "環境変数 HUGGINGFACE_API_KEY が必要"

        config["llm"]["providers"][provider_name]["max_tokens"] = 500

        config["llm"]["providers"][provider_name]["temperature"] = 0.3    }    }

        config["llm"]["providers"][provider_name]["timeout"] = 30

    }}

    save_config(config)



    print(f"\nプロバイダーを切り替えました:")

    print(f"  プロバイダー: {provider_info['name']}")

    print(f"  モデル: {model}")

    print(f"  設定ファイル: {CONFIG_FILE}\n")def load_config():def load_config():



def main():    """設定ファイルを読み込み"""    """設定ファイルを読み込み"""

    parser = argparse.ArgumentParser(description="LLMプロバイダー切り替えツール")

    parser.add_argument('provider', nargs='?', help='プロバイダー名')    if not CONFIG_FILE.exists():    if not CONFIG_FILE.exists():

    parser.add_argument('--model', '-m', help='モデル名')

    parser.add_argument('--show', '-s', action='store_true', help='現在の設定を表示')        print(f"❌ 設定ファイルが見つかりません: {CONFIG_FILE}")        print(f"❌ 設定ファイルが見つかりません: {CONFIG_FILE}")

    parser.add_argument('--list', '-l', action='store_true', help='利用可能なプロバイダーを表示')

            sys.exit(1)        sys.exit(1)

    args = parser.parse_args()



    if args.show:

        show_current()    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:

    elif args.list:

        show_available()        return yaml.safe_load(f)        return yaml.safe_load(f)

    elif args.provider:

        switch_provider(args.provider, args.model)

    else:

        parser.print_help()



if __name__ == "__main__":def save_config(config):def save_config(config):

    main()

    """設定ファイルを保存"""    """設定ファイルを保存"""

    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:

        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)





def show_current():def show_current():

    """現在の設定を表示"""    """現在の設定を表示"""

    config = load_config()    config = load_config()

    llm_config = config.get("llm", {})    llm_config = config.get("llm", {})

    providers = llm_config.get("providers", {})    providers = llm_config.get("providers", {})



    print("\n" + "="*60)    print("\n" + "="*60)

    print("📊 現在のLLM設定")    print("📊 現在のLLM設定")

    print("="*60)    print("="*60)



    enabled_providers = []    enabled_providers = []

    for provider_name, provider_config in providers.items():    for provider_name, provider_config in providers.items():

        if provider_config.get("enabled", False):        if provider_config.get("enabled", False):

            model = provider_config.get("model", "N/A")            model = provider_config.get("model", "N/A")

            priority = provider_config.get("priority", "N/A")            priority = provider_config.get("priority", "N/A")

            enabled_providers.append((priority, provider_name, model))            enabled_providers.append((priority, provider_name, model))



    if enabled_providers:    if enabled_providers:

        enabled_providers.sort(key=lambda x: x[0])        enabled_providers.sort(key=lambda x: x[0])

        print("\n✅ 有効なプロバイダー:")        print("\n✅ 有効なプロバイダー:")

        for priority, name, model in enabled_providers:        for priority, name, model in enabled_providers:

            print(f"  {priority}. {name:12} - {model}")            print(f"  {priority}. {name:12} - {model}")

    else:    else:

        print("\n⚠️  有効なプロバイダーがありません")        print("\n⚠️  有効なプロバイダーがありません")



    fallback_status = llm_config.get('default_settings', {}).get('auto_fallback', False)    print(f"\n🔄 自動フォールバック: {'ON' if llm_config.get('default_settings', {}).get('auto_fallback', False) else 'OFF'}")

    print(f"\n🔄 自動フォールバック: {'ON' if fallback_status else 'OFF'}")    print("="*60 + "\n")

    print("="*60 + "\n")



def show_available():

def show_available():    """利用可能なプロバイダーとモデルを表示"""

    """利用可能なプロバイダーとモデルを表示"""    print("\n" + "="*60)

    print("\n" + "="*60)    print("📋 利用可能なプロバイダーとモデル")

    print("📋 利用可能なプロバイダーとモデル")    print("="*60)

    print("="*60)

        for provider_id, info in PROVIDERS.items():

    for provider_id, info in PROVIDERS.items():        print(f"\n🔹 {provider_id} - {info['name']}")

        print(f"\n🔹 {provider_id} - {info['name']}")        if "note" in info:

        if "note" in info:            print(f"   ℹ️  {info['note']}")

            print(f"   ℹ️  {info['note']}")        print(f"   デフォルト: {info['default_model']}")

        print(f"   デフォルト: {info['default_model']}")        print("   利用可能モデル:")

        print("   利用可能モデル:")        for model_id, description in info['models'].items():

        for model_id, description in info['models'].items():            default_mark = "⭐" if model_id in info['default_model'] else "  "

            default_mark = "⭐" if model_id in info['default_model'] else "  "            print(f"     {default_mark} {model_id:40} - {description}")

            print(f"     {default_mark} {model_id:40} - {description}")

        print("\n" + "="*60 + "\n")

    print("\n" + "="*60 + "\n")



def switch_provider(provider_name, model=None, priority=1):

def switch_provider(provider_name, model=None, priority=1):    """プロバイダーを切り替え"""

    """プロバイダーを切り替え"""    if provider_name not in PROVIDERS:

    if provider_name not in PROVIDERS:        print(f"❌ 不明なプロバイダー: {provider_name}")

        print(f"❌ 不明なプロバイダー: {provider_name}")        print(f"利用可能: {', '.join(PROVIDERS.keys())}")

        print(f"利用可能: {', '.join(PROVIDERS.keys())}")        sys.exit(1)

        sys.exit(1)

        provider_info = PROVIDERS[provider_name]

    provider_info = PROVIDERS[provider_name]

        # モデルが指定されていない場合はデフォルトを使用

    # モデルが指定されていない場合はデフォルトを使用    if model is None:

    if model is None:        model = provider_info['default_model']

        model = provider_info['default_model']

        config = load_config()

    config = load_config()

        # LLM設定が存在しない場合は初期化

    # LLM設定が存在しない場合は初期化    if "llm" not in config:

    if "llm" not in config:        config["llm"] = {

        config["llm"] = {            "providers": {},

            "providers": {},            "default_settings": {

            "default_settings": {                "max_tokens": 200,

                "max_tokens": 200,                "temperature": 0.3,

                "temperature": 0.3,                "timeout": 30,

                "timeout": 30,                "auto_fallback": True

                "auto_fallback": True            }

            }        }

        }

        # プロバイダー設定が存在しない場合は初期化

    # プロバイダー設定が存在しない場合は初期化    if provider_name not in config["llm"]["providers"]:

    if provider_name not in config["llm"]["providers"]:        config["llm"]["providers"][provider_name] = {}

        config["llm"]["providers"][provider_name] = {}

        # 全プロバイダーを無効化

    # 全プロバイダーを無効化    for p in config["llm"]["providers"]:

    for p in config["llm"]["providers"]:        config["llm"]["providers"][p]["enabled"] = False

        config["llm"]["providers"][p]["enabled"] = False

        # 選択したプロバイダーを有効化

    # 選択したプロバイダーを有効化    config["llm"]["providers"][provider_name]["enabled"] = True

    config["llm"]["providers"][provider_name]["enabled"] = True    config["llm"]["providers"][provider_name]["model"] = model

    config["llm"]["providers"][provider_name]["model"] = model    config["llm"]["providers"][provider_name]["priority"] = priority

    config["llm"]["providers"][provider_name]["priority"] = priority

        # プロバイダー固有の設定

    # プロバイダー固有の設定    if provider_name == "ollama":

    if provider_name == "ollama":        config["llm"]["providers"][provider_name]["api_url"] = provider_info.get("api_url", "http://localhost:11434")

        api_url = provider_info.get("api_url", "http://localhost:11434")        config["llm"]["providers"][provider_name]["max_tokens"] = 500

        config["llm"]["providers"][provider_name]["api_url"] = api_url        config["llm"]["providers"][provider_name]["temperature"] = 0.3

        config["llm"]["providers"][provider_name]["max_tokens"] = 500        config["llm"]["providers"][provider_name]["timeout"] = 30

        config["llm"]["providers"][provider_name]["temperature"] = 0.3    elif provider_name == "gemini":

        config["llm"]["providers"][provider_name]["timeout"] = 30        config["llm"]["providers"][provider_name]["max_tokens"] = 2000

    elif provider_name == "gemini":        config["llm"]["providers"][provider_name]["temperature"] = 0.7

        config["llm"]["providers"][provider_name]["max_tokens"] = 2000        config["llm"]["providers"][provider_name]["timeout"] = 60

        config["llm"]["providers"][provider_name]["temperature"] = 0.7    elif provider_name == "huggingface":

        config["llm"]["providers"][provider_name]["timeout"] = 60        config["llm"]["providers"][provider_name]["max_tokens"] = 1000

    elif provider_name == "huggingface":        config["llm"]["providers"][provider_name]["temperature"] = 0.7

        config["llm"]["providers"][provider_name]["max_tokens"] = 1000        config["llm"]["providers"][provider_name"]["timeout"] = 60

        config["llm"]["providers"][provider_name]["temperature"] = 0.7

        config["llm"]["providers"][provider_name]["timeout"] = 60    save_config(config)



    save_config(config)    print(f"\n✅ プロバイダーを切り替えました:")

        print(f"   🔹 プロバイダー: {provider_info['name']}")

    print(f"\n✅ プロバイダーを切り替えました:")    print(f"   🤖 モデル: {model}")

    print(f"   🔹 プロバイダー: {provider_info['name']}")    print(f"   📊 優先度: {priority}")

    print(f"   🤖 モデル: {model}")

    print(f"   📊 優先度: {priority}")    if "note" in provider_info:

            print(f"\n   ℹ️  {provider_info['note']}")

    if "note" in provider_info:

        print(f"\n   ℹ️  {provider_info['note']}")    print(f"\n   設定ファイル: {CONFIG_FILE}")

        print()

    print(f"\n   設定ファイル: {CONFIG_FILE}")

    print()

def enable_fallback(providers_list):

    """複数プロバイダーのフォールバック設定"""

def main():    config = load_config()

    parser = argparse.ArgumentParser(

        description="LLMプロバイダー切り替えツール",    if "llm" not in config:

        formatter_class=argparse.RawDescriptionHelpFormatter,        config["llm"] = {"providers": {}, "default_settings": {}}

        epilog="""

使用例:    # 全プロバイダーを無効化

  # 現在の設定を表示    for p in config["llm"]["providers"]:

  python switch_provider.py --show        config["llm"]["providers"][p]["enabled"] = False



  # 利用可能なプロバイダーとモデルを表示    # 指定されたプロバイダーを優先度順に有効化

  python switch_provider.py --list    for i, provider_spec in enumerate(providers_list, start=1):

          parts = provider_spec.split(":", 1)

  # Ollamaに切り替え（デフォルトモデル）        provider_name = parts[0]

  python switch_provider.py ollama        model = parts[1] if len(parts) > 1 else None



  # Ollamaの特定モデルに切り替え        if provider_name not in PROVIDERS:

  python switch_provider.py ollama --model qwen2.5:0.5b-instruct            print(f"⚠️  スキップ: {provider_name} (不明なプロバイダー)")

              continue

  # Geminiに切り替え

  python switch_provider.py gemini        provider_info = PROVIDERS[provider_name]

        """        if model is None:

    )            model = provider_info['default_model']



    parser.add_argument('provider', nargs='?', help='プロバイダー名 (ollama, gemini, huggingface)')        if provider_name not in config["llm"]["providers"]:

    parser.add_argument('--model', '-m', help='モデル名')            config["llm"]["providers"][provider_name] = {}

    parser.add_argument('--priority', '-p', type=int, default=1, help='優先度 (デフォルト: 1)')

    parser.add_argument('--show', '-s', action='store_true', help='現在の設定を表示')        config["llm"]["providers"][provider_name]["enabled"] = True

    parser.add_argument('--list', '-l', action='store_true', help='利用可能なプロバイダーとモデルを表示')        config["llm"]["providers"][provider_name]["model"] = model

            config["llm"]["providers"][provider_name]["priority"] = i

    args = parser.parse_args()

        # 自動フォールバックを有効化

    if args.show:    if "default_settings" not in config["llm"]:

        show_current()        config["llm"]["default_settings"] = {}

    elif args.list:    config["llm"]["default_settings"]["auto_fallback"] = True

        show_available()

    elif args.provider:    save_config(config)

        switch_provider(args.provider, args.model, args.priority)

    else:    print(f"\n✅ フォールバック設定完了:")

        parser.print_help()    for i, provider_spec in enumerate(providers_list, start=1):

        print("\n💡 ヒント: --show で現在の設定、--list で利用可能なプロバイダーを表示")        parts = provider_spec.split(":", 1)

        provider_name = parts[0]

        model = parts[1] if len(parts) > 1 else PROVIDERS.get(provider_name, {}).get('default_model', 'N/A')

if __name__ == "__main__":        print(f"   {i}. {provider_name:12} - {model}")

    main()    print()



def main():
    parser = argparse.ArgumentParser(
        description="LLMプロバイダー切り替えツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 現在の設定を表示
  python switch_provider.py --show

  # 利用可能なプロバイダーとモデルを表示
  python switch_provider.py --list

  # Ollamaに切り替え（デフォルトモデル）
  python switch_provider.py ollama

  # Ollamaの特定モデルに切り替え
  python switch_provider.py ollama --model qwen2.5:0.5b-instruct

  # Geminiに切り替え
  python switch_provider.py gemini

  # フォールバック設定（Ollama → Gemini → HuggingFace）
  python switch_provider.py --fallback ollama gemini huggingface

  # モデル指定でフォールバック
  python switch_provider.py --fallback ollama:qwen2.5:0.5b gemini:gemini-pro
        """
    )

    parser.add_argument('provider', nargs='?', help='プロバイダー名 (ollama, gemini, huggingface)')
    parser.add_argument('--model', '-m', help='モデル名')
    parser.add_argument('--priority', '-p', type=int, default=1, help='優先度 (デフォルト: 1)')
    parser.add_argument('--show', '-s', action='store_true', help='現在の設定を表示')
    parser.add_argument('--list', '-l', action='store_true', help='利用可能なプロバイダーとモデルを表示')
    parser.add_argument('--fallback', '-f', nargs='+', metavar='PROVIDER', help='複数プロバイダーのフォールバック設定')

    args = parser.parse_args()

    if args.show:
        show_current()
    elif args.list:
        show_available()
    elif args.fallback:
        enable_fallback(args.fallback)
    elif args.provider:
        switch_provider(args.provider, args.model, args.priority)
    else:
        parser.print_help()
        print("\n💡 ヒント: --show で現在の設定、--list で利用可能なプロバイダーを表示")


if __name__ == "__main__":
    main()
