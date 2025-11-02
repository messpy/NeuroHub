#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Agent - 設定管理エージェント
YAML設定の生成、管理、LLM設定の動的更新
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.ai.llm_common import load_config, load_prompt_templates
from services.db.llm_history_manager import LLMHistoryManager


@dataclass
class LLMProviderConfig:
    """LLMプロバイダー設定"""
    name: str
    enabled: bool = True
    api_url: str = ""
    model: str = ""
    max_tokens: int = 200
    temperature: float = 0.3
    timeout: int = 30
    rate_limit: Optional[int] = None
    priority: int = 1


@dataclass
class AgentConfig:
    """エージェント設定"""
    name: str
    enabled: bool = True
    auto_mode: bool = False
    log_level: str = "INFO"
    session_timeout: int = 3600
    max_retries: int = 3


class ConfigAgent:
    """設定管理エージェント"""

    def __init__(self):
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / "config"
        self.history_manager = LLMHistoryManager()

        # 設定ファイルパス
        self.config_files = {
            "main": self.config_dir / "config.yaml",
            "llm": self.config_dir / "llm_config.yaml",
            "agent": self.config_dir / "agent_config.yaml",
            "prompts": self.config_dir / "prompt_templates.yaml"
        }

        # 現在の設定をロード
        self.current_config = self.load_all_configs()

    def load_all_configs(self) -> Dict[str, Any]:
        """全設定ファイルを読み込み"""
        configs = {}

        for config_name, config_path in self.config_files.items():
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        configs[config_name] = yaml.safe_load(f) or {}
                else:
                    configs[config_name] = {}
            except Exception as e:
                print(f"設定読み込みエラー ({config_name}): {e}")
                configs[config_name] = {}

        return configs

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """設定ファイルを保存"""
        try:
            config_path = self.config_files[config_name]
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False,
                         allow_unicode=True, sort_keys=False)

            # 現在の設定を更新
            self.current_config[config_name] = config_data
            return True

        except Exception as e:
            print(f"設定保存エラー ({config_name}): {e}")
            return False

    def generate_llm_config(self, provider_configs: List[LLMProviderConfig] = None) -> Dict[str, Any]:
        """LLM設定を生成"""

        if provider_configs is None:
            # デフォルト設定
            provider_configs = [
                LLMProviderConfig(
                    name="gemini",
                    api_url="https://generativelanguage.googleapis.com/v1beta",
                    model="gemini-2.0-flash-exp",
                    priority=1
                ),
                LLMProviderConfig(
                    name="huggingface",
                    api_url="https://api-inference.huggingface.co/v1",
                    model="meta-llama/Llama-3.2-3B-Instruct",
                    priority=2
                ),
                LLMProviderConfig(
                    name="ollama",
                    api_url="http://localhost:11434",
                    model="qwen2.5:1.5b-instruct",
                    priority=3
                )
            ]

        config = {
            "llm": {
                "providers": {},
                "provider_priority": [],
                "default_settings": {
                    "max_tokens": 200,
                    "temperature": 0.3,
                    "timeout": 30,
                    "auto_fallback": True
                },
                "logging": {
                    "enabled": True,
                    "log_level": 2,
                    "store_debug_info": True
                }
            }
        }

        # プロバイダー設定を追加
        for provider in sorted(provider_configs, key=lambda x: x.priority):
            config["llm"]["providers"][provider.name] = {
                "enabled": provider.enabled,
                "api_url": provider.api_url,
                "model": provider.model,
                "max_tokens": provider.max_tokens,
                "temperature": provider.temperature,
                "timeout": provider.timeout,
                "priority": provider.priority
            }

            if provider.rate_limit:
                config["llm"]["providers"][provider.name]["rate_limit"] = provider.rate_limit

            if provider.enabled:
                config["llm"]["provider_priority"].append(provider.name)

        return config

    def generate_agent_config(self, agent_configs: List[AgentConfig] = None) -> Dict[str, Any]:
        """エージェント設定を生成"""

        if agent_configs is None:
            # デフォルトエージェント設定
            agent_configs = [
                AgentConfig(name="git_agent", auto_mode=False),
                AgentConfig(name="llm_agent", auto_mode=True),
                AgentConfig(name="config_agent", auto_mode=False),
                AgentConfig(name="command_agent", auto_mode=False)
            ]

        config = {
            "agents": {},
            "global_settings": {
                "session_timeout": 3600,
                "auto_cleanup": True,
                "log_level": "INFO",
                "database": {
                    "path": "neurohub_llm.db",
                    "auto_backup": True,
                    "retention_days": 30
                }
            }
        }

        for agent in agent_configs:
            config["agents"][agent.name] = {
                "enabled": agent.enabled,
                "auto_mode": agent.auto_mode,
                "log_level": agent.log_level,
                "session_timeout": agent.session_timeout,
                "max_retries": agent.max_retries
            }

        return config

    def auto_detect_llm_providers(self) -> List[LLMProviderConfig]:
        """環境からLLMプロバイダーを自動検出"""
        detected_providers = []

        # Gemini検出
        if os.getenv("GEMINI_API_KEY"):
            detected_providers.append(LLMProviderConfig(
                name="gemini",
                api_url="https://generativelanguage.googleapis.com/v1beta",
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                priority=1
            ))

        # HuggingFace検出
        if os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN"):
            model = os.getenv("HF_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
            if ":" in model:  # groq形式の場合
                model_parts = model.split(":")
                if len(model_parts) >= 2:
                    model = f"{model_parts[0]}:{model_parts[1]}"

            detected_providers.append(LLMProviderConfig(
                name="huggingface",
                api_url=os.getenv("HF_API_URL", "https://api-inference.huggingface.co/v1"),
                model=model,
                priority=2
            ))

        # Ollama検出
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            import requests
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                detected_providers.append(LLMProviderConfig(
                    name="ollama",
                    api_url=ollama_host,
                    model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct"),
                    priority=3
                ))
        except:
            # Ollamaが利用できない場合もデフォルト設定は作成
            detected_providers.append(LLMProviderConfig(
                name="ollama",
                enabled=False,
                api_url=ollama_host,
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct"),
                priority=3
            ))

        return detected_providers

    def update_from_history(self) -> Dict[str, Any]:
        """履歴データから設定を最適化"""

        # プロバイダー統計を取得
        stats = self.history_manager.get_provider_stats(7)  # 過去7日

        optimization_suggestions = {
            "provider_performance": [],
            "recommended_priority": [],
            "configuration_updates": {}
        }

        for stat in stats:
            provider_name = stat['provider']
            total_requests = stat['total_requests']
            success_rate = stat['successful_requests'] / total_requests if total_requests > 0 else 0
            avg_response_time = stat['avg_response_time'] or 0

            # パフォーマンス評価
            performance_score = success_rate * 0.7 + (1.0 / (1.0 + avg_response_time / 1000)) * 0.3

            optimization_suggestions["provider_performance"].append({
                "provider": provider_name,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "performance_score": performance_score,
                "total_requests": total_requests
            })

        # 推奨優先順位
        sorted_providers = sorted(
            optimization_suggestions["provider_performance"],
            key=lambda x: x["performance_score"],
            reverse=True
        )

        optimization_suggestions["recommended_priority"] = [
            p["provider"] for p in sorted_providers if p["total_requests"] > 0
        ]

        # 設定更新提案
        for provider_perf in sorted_providers:
            provider_name = provider_perf["provider"]

            # タイムアウト調整提案
            if provider_perf["avg_response_time"] > 5000:  # 5秒以上
                optimization_suggestions["configuration_updates"][provider_name] = {
                    "timeout": min(60, provider_perf["avg_response_time"] / 1000 + 10)
                }

            # 無効化提案
            if provider_perf["success_rate"] < 0.1 and provider_perf["total_requests"] > 10:
                if provider_name not in optimization_suggestions["configuration_updates"]:
                    optimization_suggestions["configuration_updates"][provider_name] = {}
                optimization_suggestions["configuration_updates"][provider_name]["enabled"] = False

        return optimization_suggestions

    def generate_full_config(self) -> bool:
        """完全な設定ファイルセットを生成"""
        try:
            # LLMプロバイダー自動検出
            detected_providers = self.auto_detect_llm_providers()

            # 履歴ベースの最適化
            optimization = self.update_from_history()

            # 最適化を適用
            if optimization["recommended_priority"]:
                for i, provider_name in enumerate(optimization["recommended_priority"]):
                    provider = next((p for p in detected_providers if p.name == provider_name), None)
                    if provider:
                        provider.priority = i + 1

            # 設定更新を適用
            for provider_name, updates in optimization["configuration_updates"].items():
                provider = next((p for p in detected_providers if p.name == provider_name), None)
                if provider:
                    for key, value in updates.items():
                        setattr(provider, key, value)

            # LLM設定生成・保存
            llm_config = self.generate_llm_config(detected_providers)
            self.save_config("llm", llm_config)

            # エージェント設定生成・保存
            agent_config = self.generate_agent_config()
            self.save_config("agent", agent_config)

            # メイン設定更新
            main_config = self.current_config.get("main", {})
            main_config.update({
                "project_name": "NeuroHub",
                "version": "1.0.0",
                "auto_generated": True,
                "last_updated": str(Path(__file__).stat().st_mtime)
            })
            self.save_config("main", main_config)

            print("✅ 設定ファイル生成完了")
            print(f"   LLM設定: {self.config_files['llm']}")
            print(f"   エージェント設定: {self.config_files['agent']}")
            print(f"   検出プロバイダー: {len(detected_providers)}個")

            if optimization["recommended_priority"]:
                print(f"   推奨優先順位: {' > '.join(optimization['recommended_priority'])}")

            return True

        except Exception as e:
            print(f"❌ 設定生成エラー: {e}")
            return False

    def get_config_status(self) -> Dict[str, Any]:
        """設定状態を取得"""
        status = {
            "config_files": {},
            "current_config": self.current_config,
            "environment_vars": {
                "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
                "HF_TOKEN": bool(os.getenv("HF_TOKEN")),
                "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "default")
            }
        }

        for config_name, config_path in self.config_files.items():
            status["config_files"][config_name] = {
                "exists": config_path.exists(),
                "path": str(config_path),
                "size": config_path.stat().st_size if config_path.exists() else 0
            }

        return status


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Config Agent - 設定管理")
    parser.add_argument("--generate", action="store_true", help="設定ファイルを生成")
    parser.add_argument("--status", action="store_true", help="設定状態を表示")
    parser.add_argument("--optimize", action="store_true", help="履歴ベースで最適化")
    parser.add_argument("--config", choices=["llm", "agent", "main"], help="特定の設定のみ生成")

    args = parser.parse_args()

    agent = ConfigAgent()

    if args.status:
        status = agent.get_config_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))

    elif args.optimize:
        optimization = agent.update_from_history()
        print("📊 履歴ベース最適化結果:")
        print(json.dumps(optimization, ensure_ascii=False, indent=2))

    elif args.generate:
        if args.config:
            if args.config == "llm":
                providers = agent.auto_detect_llm_providers()
                config = agent.generate_llm_config(providers)
                success = agent.save_config("llm", config)
            elif args.config == "agent":
                config = agent.generate_agent_config()
                success = agent.save_config("agent", config)
            else:
                success = agent.generate_full_config()

            if success:
                print(f"✅ {args.config} 設定生成完了")
            else:
                print(f"❌ {args.config} 設定生成失敗")
        else:
            agent.generate_full_config()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
