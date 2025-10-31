#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Agent - LLM統合管理エージェント
複数のLLMプロバイダーを統合管理し、最適なプロバイダーを選択
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.llm.llm_common import (
    load_env_from_config,
    load_config,
    get_prompt_template,
    get_system_message,
    get_api_defaults,
    LLMResponse
)
from services.llm.provider_gemini import GeminiConfig
from services.llm.provider_huggingface import HuggingFaceConfig
from services.llm.provider_ollama import OllamaConfig
from services.db.llm_history_manager import LLMHistoryManager


@dataclass
class LLMRequest:
    """LLMリクエスト情報"""
    prompt: str
    system_message: str = ""
    request_type: str = "general"
    max_tokens: int = 200
    temperature: float = 0.3
    preferred_provider: Optional[str] = None
    fallback_enabled: bool = True


@dataclass
class ProviderStatus:
    """プロバイダー状態"""
    name: str
    available: bool
    configured: bool
    last_response_time: Optional[float] = None
    success_rate: float = 0.0
    error_message: Optional[str] = None


class LLMAgent:
    """LLM統合管理エージェント"""
    
    def __init__(self, config_path: str = None):
        self.project_root = project_root
        self.config = load_config()
        self.history_manager = LLMHistoryManager()
        
        # 環境設定読み込み
        load_env_from_config()
        
        # プロバイダー初期化
        self.providers = {
            'gemini': GeminiConfig(),
            'huggingface': HuggingFaceConfig(),
            'ollama': OllamaConfig()
        }
        
        # プロバイダー優先順位（設定可能）
        self.provider_priority = self.config.get('llm', {}).get('provider_priority', 
                                                               ['gemini', 'huggingface', 'ollama'])
        
        # セッション開始
        self.session_id = self.history_manager.start_session("llm_agent")
        
        # プロバイダー状態キャッシュ
        self._provider_status_cache = {}
        self._cache_ttl = 300  # 5分
        self._last_status_check = 0
    
    def check_provider_status(self, force_refresh: bool = False) -> Dict[str, ProviderStatus]:
        """全プロバイダーの状態をチェック"""
        
        current_time = time.time()
        if not force_refresh and (current_time - self._last_status_check) < self._cache_ttl:
            return self._provider_status_cache
        
        status_results = {}
        
        for name, provider in self.providers.items():
            try:
                # 設定チェック
                configured = provider.is_configured()
                
                # 接続テスト
                if configured:
                    start_time = time.time()
                    test_result = provider.test_connection()
                    response_time = time.time() - start_time
                    
                    available = test_result.get('success', False)
                    error_msg = test_result.get('error')
                else:
                    available = False
                    response_time = None
                    error_msg = "未設定"
                
                # 成功率取得（過去24時間）
                stats = self.history_manager.get_provider_stats(1)
                provider_stats = next((s for s in stats if s['provider'] == name), None)
                success_rate = 0.0
                if provider_stats and provider_stats['total_requests'] > 0:
                    success_rate = provider_stats['successful_requests'] / provider_stats['total_requests']
                
                status_results[name] = ProviderStatus(
                    name=name,
                    available=available,
                    configured=configured,
                    last_response_time=response_time,
                    success_rate=success_rate,
                    error_message=error_msg
                )
                
            except Exception as e:
                status_results[name] = ProviderStatus(
                    name=name,
                    available=False,
                    configured=False,
                    error_message=str(e)
                )
        
        self._provider_status_cache = status_results
        self._last_status_check = current_time
        
        return status_results
    
    def get_best_provider(self, request_type: str = "general") -> Optional[str]:
        """最適なプロバイダーを選択"""
        
        status = self.check_provider_status()
        
        # 利用可能なプロバイダーを優先順位でソート
        available_providers = []
        for provider_name in self.provider_priority:
            if provider_name in status and status[provider_name].available:
                available_providers.append((provider_name, status[provider_name]))
        
        if not available_providers:
            return None
        
        # 成功率と応答時間を考慮して選択
        best_provider = None
        best_score = -1
        
        for provider_name, provider_status in available_providers:
            # スコア計算（成功率を重視）
            score = provider_status.success_rate * 0.7
            
            # 応答時間ボーナス（速いほど良い）
            if provider_status.last_response_time:
                time_bonus = max(0, (5.0 - provider_status.last_response_time) / 5.0) * 0.3
                score += time_bonus
            
            if score > best_score:
                best_score = score
                best_provider = provider_name
        
        return best_provider
    
    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """テキスト生成（自動プロバイダー選択）"""
        
        start_time = time.time()
        
        # プロバイダー選択
        if request.preferred_provider and request.preferred_provider in self.providers:
            provider_order = [request.preferred_provider]
            if request.fallback_enabled:
                # フォールバック用に他のプロバイダーも追加
                other_providers = [p for p in self.provider_priority 
                                 if p != request.preferred_provider]
                provider_order.extend(other_providers)
        else:
            # 最適なプロバイダーから順番に試行
            status = self.check_provider_status()
            provider_order = [name for name in self.provider_priority 
                            if status.get(name, {}).available]
        
        last_error = None
        
        for provider_name in provider_order:
            try:
                provider = self.providers[provider_name]
                if not provider.is_configured():
                    continue
                
                # API設定取得
                api_defaults = get_api_defaults(provider_name)
                max_tokens = api_defaults.get('max_tokens', request.max_tokens)
                temperature = api_defaults.get('temperature', request.temperature)
                
                # テキスト生成
                response = provider.generate_text(
                    prompt=request.prompt,
                    system_message=request.system_message,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # 履歴に記録
                self._log_request(
                    provider_name=provider_name,
                    request=request,
                    response=response,
                    response_time=time.time() - start_time
                )
                
                if response.is_success:
                    return response
                
                last_error = response.error
                
            except Exception as e:
                last_error = str(e)
                continue
        
        # すべて失敗した場合
        error_response = LLMResponse(
            status_code=500,
            provider="none",
            model="none",
            content="",
            error=f"全プロバイダーで失敗: {last_error}",
            response_time=time.time() - start_time
        )
        
        self._log_request(
            provider_name="failed",
            request=request,
            response=error_response,
            response_time=time.time() - start_time
        )
        
        return error_response
    
    def _log_request(self, provider_name: str, request: LLMRequest, 
                    response: LLMResponse, response_time: float):
        """リクエストを履歴に記録"""
        try:
            token_counts = {}
            if hasattr(response, 'tokens_input') and response.tokens_input:
                token_counts['input'] = response.tokens_input
            if hasattr(response, 'tokens_output') and response.tokens_output:
                token_counts['output'] = response.tokens_output
            if hasattr(response, 'tokens_used') and response.tokens_used:
                token_counts['total'] = response.tokens_used
            
            debug_info = {}
            if hasattr(response, 'metadata') and response.metadata:
                debug_info = response.metadata
            
            self.history_manager.log_llm_request(
                provider=provider_name,
                model=response.model if response.model != "none" else "unknown",
                prompt_text=request.prompt,
                response_text=response.content,
                status_code=response.status_code,
                success=response.is_success,
                error_message=response.error,
                response_time_ms=int(response_time * 1000),
                token_counts=token_counts,
                debug_level=2 if response.is_success else 3,
                debug_info=debug_info,
                request_type=request.request_type
            )
        except Exception as e:
            print(f"[LLMAgent] 履歴記録エラー: {e}")
    
    def generate_commit_message(self, file_path: str, diff_content: str, 
                              detailed: bool = False) -> str:
        """コミットメッセージ生成（特化版）"""
        
        # プロンプトテンプレート取得
        template_name = "detailed_prompt" if detailed else "base_prompt"
        prompt = get_prompt_template("git_commit", template_name)
        system_msg = get_system_message("commit_message_generator")
        
        # 差分サイズ調整
        if len(diff_content) > 2000:
            lines = diff_content.split('\n')
            added = len([l for l in lines if l.startswith('+')])
            removed = len([l for l in lines if l.startswith('-')])
            diff_content = f"Large diff: +{added} -{removed} lines\n" + '\n'.join(lines[:20])
        
        full_prompt = f"{prompt}\n\n==== 対象ファイル ====\n{file_path}\n\n==== 差分 ====\n{diff_content}"
        
        request = LLMRequest(
            prompt=full_prompt,
            system_message=system_msg,
            request_type="commit_message",
            max_tokens=150,
            temperature=0.3
        )
        
        response = self.generate_text(request)
        
        if response.is_success and response.content:
            message = response.content.strip()
            # フォーマット検証
            if message.startswith(':') and len(message) <= 120:
                return message
        
        # フォールバック: スマートデフォルト
        return self._generate_smart_default(file_path, diff_content)
    
    def _generate_smart_default(self, file_path: str, diff_content: str) -> str:
        """スマートデフォルトメッセージ"""
        filename = Path(file_path).name
        
        lines = diff_content.split('\n')
        added = len([l for l in lines if l.startswith('+')])
        removed = len([l for l in lines if l.startswith('-')])
        
        if added > removed * 2:
            prefix = ":add:"
        elif removed > added * 2:
            prefix = ":fix:"
        else:
            prefix = ":update:"
        
        if filename.endswith('.py'):
            return f"{prefix} {filename} Python機能更新"
        elif filename.endswith(('.yaml', '.yml')):
            return f":config: {filename} 設定更新"
        elif filename.endswith('.md'):
            return f":docs: {filename} ドキュメント更新"
        else:
            return f"{prefix} {filename} 更新"
    
    def get_status_report(self) -> Dict[str, Any]:
        """ステータスレポート取得"""
        status = self.check_provider_status(force_refresh=True)
        stats = self.history_manager.get_provider_stats(7)
        
        return {
            "provider_status": {name: asdict(status_obj) for name, status_obj in status.items()},
            "provider_stats": stats,
            "session_id": self.session_id,
            "priority": self.provider_priority
        }
    
    def cleanup(self):
        """クリーンアップ"""
        if self.session_id:
            self.history_manager.end_session(self.session_id)


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Agent - LLM統合管理")
    parser.add_argument("--status", action="store_true", help="プロバイダー状態表示")
    parser.add_argument("--test", help="テストプロンプト")
    parser.add_argument("--provider", help="使用するプロバイダー指定")
    
    args = parser.parse_args()
    
    agent = LLMAgent()
    
    try:
        if args.status:
            report = agent.get_status_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))
        
        elif args.test:
            request = LLMRequest(
                prompt=args.test,
                system_message=get_system_message("japanese_assistant"),
                preferred_provider=args.provider
            )
            response = agent.generate_text(request)
            print(f"プロバイダー: {response.provider}")
            print(f"レスポンス: {response.content}")
            if response.error:
                print(f"エラー: {response.error}")
        
        else:
            parser.print_help()
    
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()