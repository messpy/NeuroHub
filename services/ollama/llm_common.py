#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/llm/llm_common.py
- 共通ユーティリティ: .env ロード / config.yaml ロード / Ollamaヘルスチェック
- 前提: .env はプロジェクト直下に配置する（例: ~/work/NeuroHub/.env）
"""
from __future__ import annotations
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

# プロジェクトルートを基点に固定
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
YAML_FILE = CONFIG_DIR / "config.yaml"
PROMPT_TEMPLATES_FILE = CONFIG_DIR / "prompt_templates.yaml"
ENV_FILE = PROJECT_ROOT / ".env"


# ==========================================================
# .env ロード
# ==========================================================
def load_env_from_config(debug: bool = False) -> None:
    """
    プロジェクト直下 (.env) を読み込むだけの最小実装。
    例: ~/work/NeuroHub/.env
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        if debug:
            print("[llm_common] python-dotenv 未インストール。環境読み込みスキップ。", flush=True)
        return

    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        if debug:
            print(f"[llm_common] loaded .env: {ENV_FILE}", flush=True)
    else:
        if debug:
            print(f"[llm_common] .env not found: {ENV_FILE}", flush=True)


# ==========================================================
# プロンプトテンプレート読み込み
# ==========================================================
def load_prompt_templates(path: Path | None = None) -> Dict[str, Any]:
    """prompt_templates.yaml を辞書で返す（無ければ {}）。"""
    import yaml
    p = Path(path) if path else PROMPT_TEMPLATES_FILE
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[llm_common] warn: failed to read prompt templates: {e}", flush=True)
        return {}


def get_prompt_template(template_type: str, template_name: str, **kwargs) -> str:
    """
    プロンプトテンプレートを取得してフォーマット

    Args:
        template_type: テンプレートタイプ (例: 'git_commit', 'code_analysis')
        template_name: テンプレート名 (例: 'base_prompt', 'detailed_prompt')
        **kwargs: テンプレート内のプレースホルダーを置換する値

    Returns:
        フォーマット済みのプロンプト文字列
    """
    templates = load_prompt_templates()

    try:
        template = templates.get("prompts", {}).get(template_type, {}).get(template_name, "")
        if not template:
            return f"テンプレートが見つかりません: {template_type}.{template_name}"

        # {base_prompt} などの参照を解決
        if "{base_prompt}" in template:
            base_prompt = templates.get("prompts", {}).get(template_type, {}).get("base_prompt", "")
            kwargs["base_prompt"] = base_prompt

        return template.format(**kwargs)
    except Exception as e:
        return f"テンプレート処理エラー: {e}"


def get_system_message(message_type: str) -> str:
    """システムメッセージテンプレートを取得"""
    templates = load_prompt_templates()
    return templates.get("prompts", {}).get("system_messages", {}).get(message_type, "")


def get_api_defaults(provider: str) -> Dict[str, Any]:
    """プロバイダー別のAPI デフォルト設定を取得"""
    templates = load_prompt_templates()
    return templates.get("api_defaults", {}).get(provider, {})
def load_config(path: Path | None = None) -> Dict[str, Any]:
    """config/config.yaml を辞書で返す（無ければ {}）。"""
    import yaml
    p = Path(path) if path else YAML_FILE
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[llm_common] warn: failed to read yaml: {e}", flush=True)
        return {}


# ==========================================================
# 統一レスポンス形式
# ==========================================================
@dataclass
class LLMResponse:
    """
    LLMプロバイダーからの統一レスポンス形式
    関数呼び出しや外部システムでも利用可能な詳細情報を含む
    """
    # 基本情報
    status_code: int                    # HTTPステータスコード（200, 400, 401など）
    provider: str                       # プロバイダー名（ollama, gemini, huggingface）
    model: str                          # 使用したモデル名
    content: str                        # 生成されたテキスト内容
    error: Optional[str] = None         # エラーメッセージ（ある場合）

    # 詳細メタデータ（関数呼び出し等で活用）
    metadata: Dict[str, Any] = field(default_factory=dict)

    # パフォーマンス情報
    response_time: Optional[float] = None       # レスポンス時間（秒）
    request_timestamp: Optional[str] = None     # リクエスト時刻

    # トークン情報（利用可能な場合）
    tokens_used: Optional[int] = None           # 使用トークン数
    tokens_input: Optional[int] = None          # 入力トークン数
    tokens_output: Optional[int] = None         # 出力トークン数

    # デバッグ情報
    request_url: Optional[str] = None           # リクエストURL
    request_payload: Optional[Dict] = None      # リクエストペイロード
    raw_response: Optional[Dict] = None         # 生レスポンス

    @property
    def is_success(self) -> bool:
        """成功したかどうか"""
        return self.status_code == 200 and not self.error

    @property
    def is_error(self) -> bool:
        """エラーかどうか"""
        return not self.is_success

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（関数呼び出し用）"""
        result = {
            'status_code': self.status_code,
            'provider': self.provider,
            'model': self.model,
            'content': self.content,
            'is_success': self.is_success,
            'response_time': self.response_time,
            'request_timestamp': self.request_timestamp
        }

        if self.error:
            result['error'] = self.error

        if self.tokens_used is not None:
            result['tokens_used'] = self.tokens_used

        if self.tokens_input is not None:
            result['tokens_input'] = self.tokens_input

        if self.tokens_output is not None:
            result['tokens_output'] = self.tokens_output

        if self.metadata:
            result['metadata'] = self.metadata

        return result

    def format_for_debug_level(self, debug_level: int) -> str:
        """
        デバッグレベルに応じてフォーマットされた文字列を返す
        0: コンテンツのみ
        1: 基本情報（プロバイダー、モデル、ステータス）
        2: トークン情報も含む
        3: 全詳細情報（秘密情報は除く）
        """
        if debug_level == 0:
            return self.content

        lines = []

        if debug_level >= 1:
            lines.append(f"Provider: {self.provider}")
            lines.append(f"Model: {self.model}")
            lines.append(f"Status: {self.status_code}")
            if self.response_time:
                lines.append(f"Response Time: {self.response_time:.3f}s")
            if self.error:
                lines.append(f"Error: {self.error}")
            lines.append(f"Content: {self.content}")

        if debug_level >= 2:
            if self.tokens_used is not None:
                lines.append(f"Tokens Used: {self.tokens_used}")
            if self.tokens_input is not None:
                lines.append(f"Input Tokens: {self.tokens_input}")
            if self.tokens_output is not None:
                lines.append(f"Output Tokens: {self.tokens_output}")
            if self.request_timestamp:
                lines.append(f"Timestamp: {self.request_timestamp}")

        if debug_level >= 3:
            if self.request_url:
                lines.append(f"Request URL: {self.request_url}")
            if self.metadata:
                lines.append("Metadata:")
                for key, value in self.metadata.items():
                    # 秘密情報は除外
                    if not any(secret in key.lower() for secret in ['key', 'token', 'password', 'secret']):
                        lines.append(f"  {key}: {value}")
            if self.request_payload:
                lines.append("Request Payload:")
                # 秘密情報を含む可能性があるフィールドは除外
                safe_payload = {}
                for key, value in self.request_payload.items():
                    if not any(secret in key.lower() for secret in ['key', 'token', 'password', 'secret']):
                        safe_payload[key] = value
                lines.append(f"  {json.dumps(safe_payload, ensure_ascii=False, indent=2)}")

        return "\n".join(lines)


# ==========================================================
# LLM自動履歴記録機能
# ==========================================================
def auto_log_llm_request(func):
    """
    LLM関数実行時に自動的に履歴をDBに記録するデコレータ
    """
    def wrapper(*args, **kwargs):
        from ..db.llm_history_manager import LLMHistoryManager

        # 関数実行
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            result = None
            success = False
            error_message = str(e)

        response_time_ms = int((time.time() - start_time) * 1000)

        # 履歴に記録
        try:
            manager = LLMHistoryManager()
            if not manager.current_session_id:
                manager.start_session("auto")

            # 引数から情報を抽出
            provider = kwargs.get('provider', 'unknown')
            model = kwargs.get('model', 'unknown')
            prompt = kwargs.get('prompt', str(args[0]) if args else '')
            response_text = str(result) if result else ''

            manager.log_llm_request(
                provider=provider,
                model=model,
                prompt_text=prompt[:1000],  # 長すぎる場合は切り詰め
                response_text=response_text[:1000],
                success=success,
                error_message=error_message,
                response_time_ms=response_time_ms,
                request_type=func.__name__
            )
        except Exception as log_error:
            # ログ記録エラーは無視（メイン処理に影響させない）
            print(f"[auto_log] ログ記録エラー: {log_error}", flush=True)

        if not success:
            raise Exception(error_message)

        return result

    return wrapper


def init_llm_database(db_path: str = "neurohub_llm.db") -> bool:
    """
    LLM履歴データベースを初期化

    Returns:
        初期化成功の場合True
    """
    try:
        from ..db.llm_history_manager import LLMHistoryManager
        manager = LLMHistoryManager(db_path)
        print(f"[llm_common] LLM履歴データベース初期化完了: {db_path}")
        return True
    except Exception as e:
        print(f"[llm_common] データベース初期化エラー: {e}", flush=True)
        return False
class DebugLogger:
    """極小デバッガ（stderr出力）。enabled=False なら無動作。"""
    def __init__(self, enabled: bool = False, level: int = 1) -> None:
        self.enabled = enabled
        self.level = level  # デバッグレベル (0-3)

    def dbg(self, *args) -> None:
        if self.enabled:
            try:
                import sys
                out = " ".join(str(a) for a in args)
                print(f"[debug] {out}", file=sys.stderr)
            except Exception:
                pass

    def log_response(self, response: LLMResponse) -> None:
        """LLMResponseをデバッグレベルに応じて出力"""
        if self.enabled:
            try:
                import sys
                formatted_output = response.format_for_debug_level(self.level)
                if self.level == 0:
                    # レベル0の場合は直接コンテンツを出力
                    print(formatted_output)
                else:
                    # レベル1以上の場合はデバッグ情報として出力
                    print(f"[debug] LLM Response (level {self.level}):", file=sys.stderr)
                    for line in formatted_output.split('\n'):
                        print(f"[debug] {line}", file=sys.stderr)
            except Exception:
                pass


# ==========================================================
# レスポンス作成ヘルパー関数
# ==========================================================
def create_llm_response(
    status_code: int,
    provider: str,
    model: str,
    content: str = "",
    error: Optional[str] = None,
    response_time: Optional[float] = None,
    **kwargs
) -> LLMResponse:
    """LLMResponseオブジェクトを作成するヘルパー関数"""
    from datetime import datetime

    return LLMResponse(
        status_code=status_code,
        provider=provider,
        model=model,
        content=content,
        error=error,
        response_time=response_time,
        request_timestamp=datetime.now().isoformat(),
        **kwargs
    )


# ==========================================================
# モデル名取得
# ==========================================================
def get_llm_model_from_config(cfg: Dict[str, Any], provider: str, default_model: str) -> str:
    """
    config.yaml の llm.<provider>.model を返す（なければ default_model）。
    例:
      llm:
        gemini:
          model: gemini-2.5-flash
    """
    try:
        node = (cfg or {}).get("llm", {}).get(provider, {})
        model = node.get("model") or default_model
        return str(model)
    except Exception:
        return default_model


# ==========================================================
# オプション解析（共通）
# ==========================================================
def parse_opt_kv(opts: list[str] | None) -> Dict[str, Any]:
    """
    key=value 形式のオプションリストを辞書に変換する共通関数。
    JSON風の値、boolean、数値の自動変換を行う。
    """
    if not opts:
        return {}

    import json
    out: Dict[str, Any] = {}
    for kv in opts:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        k, v = k.strip(), v.strip()

        # JSON風を優先
        try:
            if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")) or v in ("true","false","null"):
                out[k] = json.loads(v.replace("'", '"'))
                continue
        except Exception:
            pass

        # boolean判定
        if v.lower() in ("true","false"):
            out[k] = (v.lower() == "true")
            continue

        # 数値判定（int → float の順）
        try:
            out[k] = int(v)
            continue
        except ValueError:
            pass
        try:
            out[k] = float(v)
            continue
        except ValueError:
            pass

        # 文字列として扱う
        out[k] = v
    return out


# ==========================================================
# 環境確認（テスト用）
# ==========================================================
def check_environment() -> Dict[str, Any]:
    """
    LLM環境の状態をチェックする共通関数
    """
    import os

    env_status = {
        "config_file": YAML_FILE.exists(),
        "env_file": ENV_FILE.exists(),
        "tokens": {
            "gemini": bool(os.getenv("GEMINI_API_KEY")),
            "huggingface": bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")),
            "ollama": bool(os.getenv("OLLAMA_HOST")) or "localhost_default"
        },
        "config": load_config() if YAML_FILE.exists() else {}
    }

    return env_status


def print_environment_status(debug: bool = False) -> None:
    """
    環境状態を表示する
    """
    import sys

    status = check_environment()

    print("=== LLM 環境状態 ===")
    print(f"📁 設定ファイル: {YAML_FILE}")
    print(f"   存在: {'✅' if status['config_file'] else '❌'}")

    print(f"📁 環境ファイル: {ENV_FILE}")
    print(f"   存在: {'✅' if status['env_file'] else '❌'}")

    print("🔑 API トークン:")
    for provider, has_token in status['tokens'].items():
        if has_token == "localhost_default":
            print(f"   {provider}: 🔄 (デフォルト: localhost)")
        else:
            print(f"   {provider}: {'✅' if has_token else '❌'}")

    if debug and status['config']:
        print("\n📋 設定内容:")
        for key, value in status['config'].items():
            print(f"   {key}: {value}")

    print()


# ==========================================================
# 安全な文字の折り返し機能
# ==========================================================
def safe_text_wrap(text: str, max_width: int = 80, prefer_word_break: bool = True) -> str:
    """
    安全な文字の折り返し機能（日本語対応）

    Args:
        text: 折り返す文字列
        max_width: 1行の最大文字数
        prefer_word_break: 単語境界での改行を優先する（日本語では文字境界）

    Returns:
        折り返し済みの文字列
    """
    if not text or max_width <= 0:
        return text

    lines = []
    for line in text.split('\n'):
        if len(line) <= max_width:
            lines.append(line)
            continue

        # 長い行を安全に分割
        wrapped_lines = _safe_wrap_line(line, max_width, prefer_word_break)
        lines.extend(wrapped_lines)

    return '\n'.join(lines)


def _safe_wrap_line(line: str, max_width: int, prefer_word_break: bool) -> list[str]:
    """
    1行を安全に分割する内部関数

    Args:
        line: 分割する行
        max_width: 最大幅
        prefer_word_break: 単語境界優先

    Returns:
        分割された行のリスト
    """
    if len(line) <= max_width:
        return [line]

    result = []
    current_pos = 0

    while current_pos < len(line):
        # 残り文字数が最大幅以下なら、そのまま追加
        remaining = line[current_pos:]
        if len(remaining) <= max_width:
            result.append(remaining)
            break

        # 切断位置を決定
        cut_pos = _find_safe_cut_position(
            line, current_pos, current_pos + max_width, prefer_word_break
        )

        # 安全に切断できない場合は強制切断
        if cut_pos <= current_pos:
            cut_pos = current_pos + max_width

        result.append(line[current_pos:cut_pos])
        current_pos = cut_pos

    return result


def _find_safe_cut_position(line: str, start: int, max_end: int, prefer_word_break: bool) -> int:
    """
    安全な切断位置を見つける

    Args:
        line: 対象行
        start: 開始位置
        max_end: 最大終了位置
        prefer_word_break: 単語境界優先

    Returns:
        切断位置
    """
    if max_end >= len(line):
        return len(line)

    # 単語境界優先の場合
    if prefer_word_break:
        # 英語の単語境界を探す（スペース、ハイフン等）
        for i in range(max_end, start, -1):
            if i < len(line) and line[i] in ' \t-_.,;:!?':
                return i + 1

        # 日本語の場合は句読点や助詞の後を探す
        japanese_breaks = '。、！？：；）】」』｝〉》'
        for i in range(max_end, start, -1):
            if i < len(line) and line[i] in japanese_breaks:
                return i + 1

        # 漢字→ひらがな、ひらがな→カタカナ等の境界を探す
        for i in range(max_end - 1, start, -1):
            if i < len(line) - 1:
                current_char = line[i]
                next_char = line[i + 1]

                # 文字種の境界を判定
                if _is_char_boundary(current_char, next_char):
                    return i + 1

    # 適切な境界が見つからない場合は最大位置
    return max_end


def _is_char_boundary(char1: str, char2: str) -> bool:
    """
    2つの文字の間が適切な境界かどうかを判定

    Args:
        char1: 前の文字
        char2: 後の文字

    Returns:
        境界として適切かどうか
    """
    import unicodedata

    def get_char_type(char):
        """文字の種類を判定"""
        if char.isascii():
            if char.isalpha():
                return 'latin'
            elif char.isdigit():
                return 'digit'
            else:
                return 'symbol'

        # Unicode カテゴリで判定
        category = unicodedata.category(char)
        name = unicodedata.name(char, '').upper()

        if 'HIRAGANA' in name:
            return 'hiragana'
        elif 'KATAKANA' in name:
            return 'katakana'
        elif category == 'Lo':  # Other Letter (通常は漢字)
            return 'kanji'
        elif category.startswith('P'):  # Punctuation
            return 'punct'
        else:
            return 'other'

    type1 = get_char_type(char1)
    type2 = get_char_type(char2)

    # 異なる文字種の境界は適切
    if type1 != type2:
        return True

    # 句読点の後は適切
    if type1 == 'punct':
        return True

    return False


def truncate_text_safely(text: str, max_length: int, suffix: str = "...") -> str:
    """
    文字列を安全に切り詰める（文字境界を考慮）

    Args:
        text: 対象文字列
        max_length: 最大長さ
        suffix: 切り詰め時に追加する接尾辞

    Returns:
        切り詰め済み文字列
    """
    if not text or len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return suffix[:max_length]

    target_length = max_length - len(suffix)

    # 文字境界を考慮して切り詰め位置を調整
    cut_pos = _find_safe_cut_position(text, 0, target_length, prefer_word_break=True)

    if cut_pos <= 0:
        cut_pos = target_length

    return text[:cut_pos] + suffix


def validate_text_length(text: str, max_length: int, field_name: str = "text") -> tuple[bool, str]:
    """
    テキスト長を検証し、超過時は警告メッセージを返す

    Args:
        text: 検証するテキスト
        max_length: 最大長さ
        field_name: フィールド名（エラーメッセージ用）

    Returns:
        (検証結果, エラーメッセージ)
    """
    if not text:
        return True, ""

    if len(text) <= max_length:
        return True, ""

    return False, f"{field_name}の長さが上限({max_length}文字)を超えています: {len(text)}文字"


# ==========================================================
# 共通LLMプロバイダー基底クラス
# ==========================================================
class LLMProviderConfig:
    """
    LLMプロバイダーの共通基底クラス

    注意：各プロバイダーは独自の詳細実装を維持できます
    単体テストや詳細な情報取得のため、共通化しすぎないようにします
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.cfg = load_config()

    def get_model_from_config(self, default_model: str) -> str:
        """config.yamlからモデル名を取得"""
        return get_llm_model_from_config(self.cfg, self.provider_name, default_model)

    def is_configured(self) -> bool:
        """設定が有効かチェック（サブクラスで実装）"""
        raise NotImplementedError

    def get_api_url(self, model: str = None) -> str:
        """API URLを生成（サブクラスで実装）"""
        raise NotImplementedError

    def build_payload(self, text: str, opts: Dict[str, Any] = None) -> Dict[str, Any]:
        """リクエストペイロードを構築（サブクラスで実装）"""
        raise NotImplementedError

    def format_error_hint(self, status_code: int, response_text: str, url: str, model: str) -> str:
        """APIエラー時のヒントを生成"""
        hints = []

        if status_code == 401:
            hints.append(f"🔑 認証エラー: {self.provider_name.upper()}_API_KEY を確認してください")
        elif status_code == 403:
            hints.append(f"🚫 アクセス拒否: API キーの権限またはプランを確認してください")
        elif status_code == 404:
            hints.append(f"🔍 リソース未発見:")
            hints.append(f"   モデル: {model}")
            hints.append(f"   URL: {url}")
            hints.append(f"   → モデル名が正しいか確認してください")
        elif status_code == 429:
            hints.append(f"⏰ レート制限: しばらく待ってから再試行してください")
        elif status_code == 500:
            hints.append(f"🔧 サーバーエラー: {self.provider_name} 側の問題の可能性があります")
        elif status_code >= 400:
            hints.append(f"⚠️  クライアントエラー (HTTP {status_code})")
            hints.append(f"   モデル: {model}")
            hints.append(f"   URL: {url}")

        if "invalid" in response_text.lower() or "not found" in response_text.lower():
            hints.append(f"💡 利用可能なモデル一覧を確認することをお勧めします")

        return "\n".join(hints)


def make_api_request(url: str, payload: Dict[str, Any], headers: Dict[str, str],
                    timeout: int, provider_config: LLMProviderConfig,
                    model: str, debug_logger: DebugLogger = None) -> LLMResponse:
    """
    共通API リクエスト処理（オプショナル）

    各プロバイダーは独自の詳細実装を維持できます。
    この関数は共通ユーティリティとして提供されますが、
    単体テストや詳細情報取得のため、使用は必須ではありません。

    戻り値: LLMResponse オブジェクト
    """
    import requests

    start_time = time.time()

    try:
        if debug_logger:
            debug_logger.dbg("POST", url)
            debug_logger.dbg("payload", json.dumps(payload, ensure_ascii=False))

        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response_time = time.time() - start_time

        if resp.status_code != 200:
            error_hint = provider_config.format_error_hint(
                resp.status_code, resp.text, url, model
            )
            error_msg = f"HTTP {resp.status_code}:\n{error_hint}\n\nResponse: {resp.text}"

            return create_llm_response(
                status_code=resp.status_code,
                provider=provider_config.provider_name,
                model=model,
                content="",
                error=error_msg,
                response_time=response_time,
                request_url=url,
                request_payload=payload,
                raw_response={"status_code": resp.status_code, "text": resp.text}
            )

        data = resp.json()

        return create_llm_response(
            status_code=200,
            provider=provider_config.provider_name,
            model=model,
            content="",  # プロバイダー固有の処理で設定される
            response_time=response_time,
            request_url=url,
            request_payload=payload,
            raw_response=data
        )

    except Exception as e:
        response_time = time.time() - start_time
        error_msg = f"Request failed: {e}\nURL: {url}\nModel: {model}"

        return create_llm_response(
            status_code=500,
            provider=provider_config.provider_name,
            model=model,
            content="",
            error=error_msg,
            response_time=response_time,
            request_url=url,
            request_payload=payload
        )
