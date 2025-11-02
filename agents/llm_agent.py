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
from typing import Dict, List, Optional, Any, Union, Union
from dataclasses import dataclass, asdict

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import traceback
from typing import Optional, Dict
from pathlib import Path
from agents.common import BaseAgent
from agents.config_agent import AgentConfig

from services.llm.llm_common import (
    load_env_from_config,
    load_config,
    get_prompt_template,
    get_system_message,
    get_api_defaults,
    LLMResponse
)
# Ollama統一（他のプロバイダーは将来分離予定）
from services.llm.provider_ollama import OllamaConfig
from services.db.llm_history_manager import LLMHistoryManager


@dataclass
@dataclass
class LLMRequest:
    """LLMリクエスト情報"""
    prompt: str
    system_message: str = ""
    request_type: str = "general"
    max_tokens: int = 4000  # コード生成に十分なトークン数
    temperature: float = 0.3
    preferred_provider: Optional[str] = None
    fallback_enabled: bool = True
    get_all_responses: bool = False  # 全プロバイダーからレスポンス取得


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

    def __init__(self, config_path: str = None, provider: str = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス
            provider: 優先プロバイダー ('gemini', 'ollama', 'huggingface')
        """
        self.project_root = project_root
        self.config = load_config()
        self.history_manager = LLMHistoryManager()

        # 環境設定読み込み
        load_env_from_config()

        # プロバイダー初期化（Ollama統一）
        self.providers = {
            'ollama': OllamaConfig()
            # 将来的に他のプロバイダーもサポート予定
        }

        # プロバイダー優先順位（Ollama固定）
        if provider and provider == 'ollama':
            self.provider_priority = ['ollama']
        else:
            self.provider_priority = self.config.get('llm', {}).get('provider_priority', ['ollama'])

        # セッション開始
        self.session_id = self.history_manager.start_session("llm_agent")

        # プロバイダー状態キャッシュ
        self._provider_status_cache = {}
        self._cache_ttl = 300  # 5分
        self._last_status_check = 0

    def get_first_available_provider(self) -> Optional[str]:
        """最初に利用可能なプロバイダーを取得（高速版）"""
        for name in self.provider_priority:
            provider = self.providers.get(name)
            if provider and provider.is_configured():
                try:
                    # 軽量な接続チェック
                    if provider.test_connection():
                        return name
                except Exception:
                    continue
        return None

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

                    # test_connectionはboolを返すため、直接使用
                    available = bool(test_result)
                    error_msg = None if available else "接続テスト失敗"
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

    def generate_text(self, request: LLMRequest) -> Union[LLMResponse, Dict[str, LLMResponse]]:
        """テキスト生成（自動プロバイダー選択）"""

        # 全プロバイダーからレスポンス取得の場合
        if request.get_all_responses:
            return self.generate_text_all_providers(request)

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
            # 最適なプロバイダーから順番に試行（最適化版）
            if request.fallback_enabled:
                # フォールバック有効時は全体チェック
                status = self.check_provider_status()
                provider_order = [name for name in self.provider_priority
                                if status.get(name, {}).available]
            else:
                # フォールバック無効時は最初の利用可能なプロバイダーのみ
                first_available = self.get_first_available_provider()
                provider_order = [first_available] if first_available else []

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

                # テキスト生成（プロバイダーに応じて適切なメソッド呼び出し）
                if hasattr(provider, 'generate_text'):
                    response = provider.generate_text(
                        prompt=request.prompt,
                        system_message=request.system_message,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                elif hasattr(provider, 'infer'):
                    # inferメソッドを使用（Gemini, HuggingFace, Ollama）
                    opts = {
                        'max_tokens': max_tokens,
                        'temperature': temperature
                    }

                    if provider_name == 'ollama':
                        # Ollamaはoptsを受け取らない
                        response = provider.infer(request.prompt)
                    else:
                        # Gemini, HuggingFaceはoptsを受け取る
                        if provider_name == 'huggingface' and request.system_message:
                            response = provider.infer(
                                request.prompt,
                                opts=opts,
                                system_text=request.system_message
                            )
                        else:
                            response = provider.infer(
                                request.prompt,
                                opts=opts
                            )
                else:
                    raise AttributeError(f"Provider {provider_name} has no generate_text or infer method")

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
        """リクエストを履歴に記録（エラー耐性強化版）"""
        try:
            # 安全なトークン数取得
            token_counts = {}
            try:
                if hasattr(response, 'tokens_input') and response.tokens_input:
                    token_counts['input'] = int(response.tokens_input)
                if hasattr(response, 'tokens_output') and response.tokens_output:
                    token_counts['output'] = int(response.tokens_output)
                if hasattr(response, 'tokens_used') and response.tokens_used:
                    token_counts['total'] = int(response.tokens_used)
            except (ValueError, TypeError) as e:
                if self.debug:
                    print(f"[LLMAgent] トークン数解析エラー: {e}")

            # 安全なメタデータ取得
            debug_info = {}
            try:
                if hasattr(response, 'metadata') and response.metadata:
                    # 機密情報を除外した安全なメタデータ
                    for key, value in response.metadata.items():
                        if not any(secret in key.lower() for secret in ['key', 'token', 'password', 'secret']):
                            debug_info[key] = str(value)[:500]  # 長すぎる値は切り詰め
            except Exception as e:
                if self.debug:
                    print(f"[LLMAgent] メタデータ処理エラー: {e}")

            # 安全な文字列処理
            safe_prompt = str(request.prompt)[:1000] if request.prompt else ""
            safe_response = str(response.content)[:2000] if response.content else ""
            safe_error = str(response.error)[:500] if response.error else None
            safe_model = str(response.model) if response.model and response.model != "none" else "unknown"

            # 履歴記録実行
            self.history_manager.log_llm_request(
                provider=provider_name,
                model=safe_model,
                prompt_text=safe_prompt,
                response_text=safe_response,
                status_code=int(response.status_code),
                success=bool(response.is_success),
                error_message=safe_error,
                response_time_ms=max(0, int(response_time * 1000)),
                token_counts=token_counts,
                debug_level=2 if response.is_success else 3,
                debug_info=debug_info,
                request_type=str(request.request_type) if request.request_type else "unknown"
            )
        except Exception as e:
            # ログ記録失敗は致命的ではないため、警告のみ
            error_msg = f"[LLMAgent] 履歴記録エラー: {type(e).__name__}: {e}"
            print(error_msg)
            if self.debug:
                import traceback
                print(f"[LLMAgent] 詳細: {traceback.format_exc()}")

    def generate_text_chunked(self, text: str, chunk_size: int = 500,
                             instruction: str = "要約してください",
                             combine_instruction: str = "以下の要約を統合してください") -> LLMResponse:
        """
        長いテキストをチャンクに分割してAI処理し、結果を結合（エラー耐性強化版）

        Args:
            text: 処理対象のテキスト
            chunk_size: チャンクサイズ（文字数）
            instruction: 各チャンクに対する指示
            combine_instruction: 結果統合時の指示
        """
        # 入力検証
        if not text or not isinstance(text, str):
            return LLMResponse(
                status_code=400,
                provider="chunked_error",
                model="validation",
                content="",
                error="無効な入力テキスト"
            )

        if chunk_size <= 0:
            chunk_size = 500

        if len(text.strip()) <= chunk_size:
            # チャンク分割不要
            request = LLMRequest(
                prompt=f"{instruction}\n\n{text}",
                system_message="日本語で簡潔に回答してください",
                max_tokens=min(len(text) // 2 + 50, 200),
                temperature=0.1
            )
            return self.generate_text(request)

        try:
            # 安全なチャンク分割
            chunks = []
            current_pos = 0

            while current_pos < len(text):
                end_pos = min(current_pos + chunk_size, len(text))

                # 文字境界を考慮した切断位置調整
                if end_pos < len(text):
                    # 句読点での切断を優先
                    for i in range(end_pos, max(current_pos, end_pos - 50), -1):
                        if text[i] in '。、！？\n':
                            end_pos = i + 1
                            break

                chunk = text[current_pos:end_pos].strip()
                if chunk:
                    chunks.append(chunk)
                current_pos = end_pos

            if self.debug:
                print(f"📝 テキストを{len(chunks)}個のチャンクに分割して処理中...")

            # 各チャンクを処理（エラー耐性強化）
            chunk_results = []
            successful_chunks = 0

            for i, chunk in enumerate(chunks):
                try:
                    if self.debug:
                        print(f"   🔄 チャンク {i+1}/{len(chunks)} 処理中...")

                    request = LLMRequest(
                        prompt=f"{instruction}\n\n{chunk}",
                        system_message="日本語で簡潔に回答してください",
                        max_tokens=min(len(chunk) // 3 + 30, 150),
                        temperature=0.1
                    )

                    response = self.generate_text(request)
                    if response.is_success and response.content:
                        chunk_results.append(response.content.strip())
                        successful_chunks += 1
                    else:
                        # 失敗時は原文の要約を代用
                        fallback_content = chunk[:100] + "..." if len(chunk) > 100 else chunk
                        chunk_results.append(f"[原文: {fallback_content}]")

                except Exception as e:
                    error_msg = f"[チャンク{i+1}エラー: {e}]"
                    chunk_results.append(error_msg)
                    if self.debug:
                        print(f"   ❌ {error_msg}")

            # 成功率チェック
            success_rate = successful_chunks / len(chunks) if chunks else 0
            if success_rate < 0.3:  # 成功率30%未満は失敗とみなす
                return LLMResponse(
                    status_code=500,
                    provider="chunked_error",
                    model="processing",
                    content="",
                    error=f"チャンク処理成功率が低すぎます: {success_rate:.1%}"
                )

            # 結果を統合
            if len(chunk_results) > 1:
                try:
                    if self.debug:
                        print(f"   🔄 {len(chunk_results)}個の結果を統合中...")

                    # 統合テキストの長さ制限
                    combined_items = []
                    total_length = 0
                    max_combined_length = 1500  # 統合テキストの最大長

                    for i, result in enumerate(chunk_results):
                        item = f"結果{i+1}: {result}"
                        if total_length + len(item) <= max_combined_length:
                            combined_items.append(item)
                            total_length += len(item)
                        else:
                            # 長すぎる場合は残りを省略
                            combined_items.append(f"...他{len(chunk_results)-i}件")
                            break

                    combined_text = "\n".join(combined_items)

                    final_request = LLMRequest(
                        prompt=f"{combine_instruction}\n\n{combined_text}",
                        system_message="統合結果を日本語で簡潔に回答してください",
                        max_tokens=min(len(combined_text) // 4 + 50, 200),
                        temperature=0.1
                    )

                    final_response = self.generate_text(final_request)
                    if final_response.is_success:
                        # 成功情報をメタデータに追加
                        final_response.metadata = final_response.metadata or {}
                        final_response.metadata.update({
                            'chunk_count': len(chunks),
                            'successful_chunks': successful_chunks,
                            'success_rate': f"{success_rate:.1%}"
                        })
                        return final_response
                    else:
                        # 統合失敗時は最良の結果を返す
                        best_result = max(chunk_results, key=len) if chunk_results else "処理失敗"
                        return LLMResponse(
                            status_code=200,
                            provider="chunked_fallback",
                            model="best_chunk",
                            content=best_result,
                            metadata={'fallback_reason': '統合処理失敗'}
                        )

                except Exception as e:
                    # 統合処理例外
                    best_result = chunk_results[0] if chunk_results else "処理失敗"
                    return LLMResponse(
                        status_code=200,
                        provider="chunked_error",
                        model="exception_fallback",
                        content=best_result,
                        error=f"統合処理例外: {e}"
                    )
            else:
                # チャンクが1個だけの場合
                result_content = chunk_results[0] if chunk_results else "処理失敗"
                return LLMResponse(
                    status_code=200 if chunk_results else 500,
                    provider="chunked_single",
                    model="single_chunk",
                    content=result_content,
                    metadata={'chunk_count': 1}
                )

        except Exception as e:
            # 全体的な例外処理
            return LLMResponse(
                status_code=500,
                provider="chunked_critical_error",
                model="exception",
                content="",
                error=f"チャンク処理で予期しないエラー: {e}"
            )
            return self.generate_text(request)

        # チャンク分割
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            chunks.append(chunk)

        print(f"📝 テキストを{len(chunks)}個のチャンクに分割して処理中...")

        # 各チャンクを処理
        chunk_results = []
        for i, chunk in enumerate(chunks):
            print(f"   🔄 チャンク {i+1}/{len(chunks)} 処理中...")

            request = LLMRequest(
                prompt=f"{instruction}\n\n{chunk}",
                system_message="日本語で簡潔に回答してください",
                max_tokens=80,
                temperature=0.1
            )

            response = self.generate_text(request)
            if response.is_success and response.content:
                chunk_results.append(response.content.strip())
            else:
                chunk_results.append(f"[チャンク{i+1}処理失敗]")

        # 結果を統合
        if len(chunk_results) > 1:
            print(f"   🔄 {len(chunk_results)}個の結果を統合中...")
            combined_text = "\n".join([f"結果{i+1}: {result}" for i, result in enumerate(chunk_results)])

            final_request = LLMRequest(
                prompt=f"{combine_instruction}\n\n{combined_text}",
                system_message="統合結果を日本語で簡潔に回答してください",
                max_tokens=100,
                temperature=0.1
            )

            final_response = self.generate_text(final_request)
            if final_response.is_success:
                return final_response
            else:
                # 統合失敗時は最初の結果を返す
                return LLMResponse(
                    content=chunk_results[0] if chunk_results else "処理失敗",
                    is_success=bool(chunk_results),
                    provider="chunked_fallback",
                    response_time=0.0
                )
        else:
            # チャンクが1個だけの場合
            return LLMResponse(
                content=chunk_results[0] if chunk_results else "処理失敗",
                is_success=bool(chunk_results),
                provider="chunked_single",
                response_time=0.0
            )
        """全プロバイダーからレスポンスを取得"""

        responses = {}
        status = self.check_provider_status()

        for provider_name in self.provider_priority:
            if not status.get(provider_name, {}).available:
                continue

            try:
                provider = self.providers[provider_name]
                if not provider.is_configured():
                    continue

                # API設定取得
                api_defaults = get_api_defaults(provider_name)
                max_tokens = api_defaults.get('max_tokens', request.max_tokens)
                temperature = api_defaults.get('temperature', request.temperature)

                # テキスト生成
                if hasattr(provider, 'generate_text'):
                    response = provider.generate_text(
                        prompt=request.prompt,
                        system_message=request.system_message,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                elif hasattr(provider, 'infer'):
                    opts = {
                        'max_tokens': max_tokens,
                        'temperature': temperature
                    }

                    if provider_name == 'ollama':
                        response = provider.infer(request.prompt)
                    else:
                        if provider_name == 'huggingface' and request.system_message:
                            response = provider.infer(
                                request.prompt,
                                opts=opts,
                                system_text=request.system_message
                            )
                        else:
                            response = provider.infer(
                                request.prompt,
                                opts=opts
                            )
                else:
                    continue

                responses[provider_name] = response

            except Exception as e:
                # エラーレスポンスを作成
                from services.llm.llm_common import create_llm_response
                error_response = create_llm_response(
                    status_code=500,
                    provider=provider_name,
                    model="unknown",
                    content="",
                    error=str(e),
                    response_time=0.0
                )
                responses[provider_name] = error_response

        return responses

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

    # チャンク処理関連オプション
    parser.add_argument("--chunk", type=int, help="チャンクサイズ（文字数）")
    parser.add_argument("--file", help="入力ファイルパス（チャンク処理用）")
    parser.add_argument("--text", help="入力テキスト（チャンク処理用）")
    parser.add_argument("--instruction", default="要約してください", help="各チャンクへの指示")

    args = parser.parse_args()

    agent = LLMAgent()

    try:
        if args.status:
            report = agent.get_status_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))

        elif args.chunk:
            # チャンク処理モード
            if args.file:
                try:
                    with open(args.file, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception as e:
                    print(f"ファイル読み込みエラー: {e}")
                    return
            elif args.text:
                text = args.text
            else:
                print("--file または --text を指定してください")
                return

            print(f"📝 チャンク処理開始 (サイズ: {args.chunk}文字)")
            response = agent.generate_text_chunked(
                text=text,
                chunk_size=args.chunk,
                instruction=args.instruction
            )

            print(f"\n✅ 処理完了")
            print(f"プロバイダー: {response.provider}")
            print(f"結果:\n{response.content}")
            if response.error:
                print(f"エラー: {response.error}")

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
