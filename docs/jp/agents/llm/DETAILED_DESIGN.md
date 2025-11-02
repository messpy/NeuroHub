# LLMエージェント 詳細設計

## 🏗️ クラス構造

### LLMAgent クラス

**ファイル**: `agents/llm_agent.py`

#### 責任
- 複数LLMプロバイダーの統合管理
- プロバイダー自動選択・フォールバック
- リクエスト・レスポンス管理
- 履歴記録

---

## 📊 データモデル

### 1. LLMRequest（データクラス）

```python
@dataclass
class LLMRequest:
    """LLMリクエスト情報"""
    prompt: str                              # プロンプト本文
    system_message: str = ""                 # システムメッセージ
    request_type: str = "general"            # リクエストタイプ
    max_tokens: int = 4000                   # 最大トークン数
    temperature: float = 0.3                 # 温度パラメータ
    preferred_provider: Optional[str] = None # 優先プロバイダー
    fallback_enabled: bool = True            # フォールバック有効化
    get_all_responses: bool = False          # 全プロバイダー取得
```

**使用例**:
```python
request = LLMRequest(
    prompt="Pythonでフィボナッチ数列を実装して",
    system_message="あなたは優秀なPythonプログラマーです",
    request_type="code_generation",
    temperature=0.1  # コード生成は低温度
)
```

### 2. ProviderStatus（データクラス）

```python
@dataclass
class ProviderStatus:
    """プロバイダー状態"""
    name: str                                # プロバイダー名
    available: bool                          # 利用可能性
    configured: bool                         # 設定完了
    last_response_time: Optional[float]      # 最終応答時間
    success_rate: float = 0.0                # 成功率
    error_message: Optional[str] = None      # エラーメッセージ
```

### 3. LLMResponse（データクラス）

**場所**: `services/ai/llm_common.py`

```python
@dataclass
class LLMResponse:
    """LLM応答情報"""
    content: str                             # 応答本文
    provider: str                            # 使用プロバイダー
    model: str                               # 使用モデル
    tokens: int                              # トークン数
    latency: float                           # レイテンシ（秒）
    success: bool                            # 成功フラグ
    error: Optional[str] = None              # エラー情報
```

---

## 🔧 主要メソッド

### 初期化

#### `__init__(config_path: str = None, provider: str = None)`

```python
def __init__(self, config_path: str = None, provider: str = None):
    """
    初期化

    Args:
        config_path: 設定ファイルパス（デフォルト: config/llm_config.yaml）
        provider: 優先プロバイダー（'ollama', 'gemini', 'huggingface'）
    """
    # 1. プロジェクトルート設定
    self.project_root = Path(__file__).parent.parent

    # 2. 設定ファイル読み込み
    self.config = load_config(config_path)

    # 3. 環境変数読み込み
    load_env_from_config()

    # 4. プロバイダー初期化
    self.providers = {
        'ollama': OllamaProvider(),
        'gemini': GeminiProvider(),
        'huggingface': HuggingFaceProvider()
    }

    # 5. 優先順位設定
    self.provider_priority = self._set_priority(provider)

    # 6. 履歴管理初期化
    self.history_manager = LLMHistoryManager()
    self.session_id = self.history_manager.start_session("llm_agent")
```

---

### プロバイダー管理

#### `get_available_providers() -> List[str]`

```python
def get_available_providers(self) -> List[str]:
    """
    利用可能なプロバイダー一覧を取得

    Returns:
        利用可能なプロバイダー名リスト
    """
    available = []
    for name, provider in self.providers.items():
        if provider.is_available() and provider.is_configured():
            available.append(name)
    return available
```

#### `set_provider_priority(priority: List[str])`

```python
def set_provider_priority(self, priority: List[str]):
    """
    プロバイダー優先順位を設定

    Args:
        priority: プロバイダー名リスト（優先順）

    Example:
        agent.set_provider_priority(["gemini", "ollama", "huggingface"])
    """
    self.provider_priority = [p for p in priority if p in self.providers]
```

#### `get_provider_status(provider: str) -> ProviderStatus`

```python
def get_provider_status(self, provider: str) -> ProviderStatus:
    """
    プロバイダー状態を取得

    Args:
        provider: プロバイダー名

    Returns:
        ProviderStatus オブジェクト
    """
    # キャッシュチェック
    if self._is_cache_valid():
        return self._provider_status_cache.get(provider)

    # 状態取得
    provider_obj = self.providers.get(provider)
    if not provider_obj:
        return ProviderStatus(
            name=provider,
            available=False,
            configured=False,
            error_message="Provider not found"
        )

    status = ProviderStatus(
        name=provider,
        available=provider_obj.is_available(),
        configured=provider_obj.is_configured(),
        success_rate=self._calculate_success_rate(provider)
    )

    # キャッシュ更新
    self._provider_status_cache[provider] = status
    return status
```

---

### リクエスト処理

#### `generate_response(prompt: str, **kwargs) -> str`

```python
def generate_response(
    self,
    prompt: str,
    system_message: str = "",
    provider: Optional[str] = None,
    **kwargs
) -> str:
    """
    プロンプトから応答を生成

    Args:
        prompt: プロンプト本文
        system_message: システムメッセージ
        provider: 優先プロバイダー（Noneの場合は自動選択）
        **kwargs: 追加パラメータ

    Returns:
        生成された応答テキスト

    Raises:
        RuntimeError: 全プロバイダーで失敗した場合
    """
    # LLMRequestオブジェクト作成
    request = LLMRequest(
        prompt=prompt,
        system_message=system_message,
        preferred_provider=provider,
        **kwargs
    )

    # プロバイダー選択
    selected_provider = self._select_provider(request)

    # リクエスト実行
    response = self._execute_request(selected_provider, request)

    # 履歴記録
    self._save_to_history(request, response)

    return response.content
```

#### `generate_response_with_fallback(prompt: str, **kwargs) -> str`

```python
def generate_response_with_fallback(
    self,
    prompt: str,
    **kwargs
) -> str:
    """
    フォールバック機能付き応答生成

    優先順位に従って複数プロバイダーを試行し、
    最初に成功したプロバイダーの応答を返す

    Args:
        prompt: プロンプト本文
        **kwargs: 追加パラメータ

    Returns:
        生成された応答テキスト

    Raises:
        RuntimeError: 全プロバイダーで失敗
    """
    errors = {}

    for provider_name in self.provider_priority:
        try:
            # プロバイダー状態確認
            status = self.get_provider_status(provider_name)
            if not status.available or not status.configured:
                continue

            # リクエスト実行
            response = self.generate_response(
                prompt=prompt,
                provider=provider_name,
                **kwargs
            )

            return response

        except Exception as e:
            errors[provider_name] = str(e)
            continue

    # 全プロバイダーで失敗
    error_msg = "\n".join([f"{k}: {v}" for k, v in errors.items()])
    raise RuntimeError(f"全プロバイダーで失敗:\n{error_msg}")
```

---

### モデル管理

#### `list_models(provider: str = None) -> List[str]`

```python
def list_models(self, provider: str = None) -> List[str]:
    """
    利用可能なモデル一覧を取得

    Args:
        provider: プロバイダー名（Noneの場合は全プロバイダー）

    Returns:
        モデル名リスト
    """
    if provider:
        provider_obj = self.providers.get(provider)
        if provider_obj:
            return provider_obj.list_models()
        return []

    # 全プロバイダーのモデル一覧
    all_models = {}
    for name, provider_obj in self.providers.items():
        try:
            models = provider_obj.list_models()
            all_models[name] = models
        except Exception as e:
            all_models[name] = []

    return all_models
```

#### `switch_model(provider: str, model: str)`

```python
def switch_model(self, provider: str, model: str):
    """
    使用モデルを切り替え

    Args:
        provider: プロバイダー名
        model: モデル名

    Raises:
        ValueError: プロバイダーまたはモデルが存在しない
    """
    provider_obj = self.providers.get(provider)
    if not provider_obj:
        raise ValueError(f"プロバイダー '{provider}' が存在しません")

    # モデル存在確認
    available_models = provider_obj.list_models()
    if model not in available_models:
        raise ValueError(
            f"モデル '{model}' は利用できません。"
            f"利用可能: {available_models}"
        )

    # モデル切り替え
    provider_obj.set_model(model)
```

---

### 内部メソッド

#### `_select_provider(request: LLMRequest) -> str`

```python
def _select_provider(self, request: LLMRequest) -> str:
    """
    最適なプロバイダーを選択

    選択基準:
    1. preferred_providerが指定されている場合はそれを優先
    2. 利用可能性・設定状態をチェック
    3. success_rateが高いプロバイダーを選択
    4. last_response_timeが短いプロバイダーを選択
    """
    # 優先プロバイダー指定
    if request.preferred_provider:
        status = self.get_provider_status(request.preferred_provider)
        if status.available and status.configured:
            return request.preferred_provider

    # 自動選択
    best_provider = None
    best_score = -1

    for provider_name in self.provider_priority:
        status = self.get_provider_status(provider_name)

        if not status.available or not status.configured:
            continue

        # スコア計算（成功率重視）
        score = status.success_rate * 0.7
        if status.last_response_time:
            # レスポンス時間も考慮（速いほど高スコア）
            score += (1.0 / max(status.last_response_time, 0.1)) * 0.3

        if score > best_score:
            best_score = score
            best_provider = provider_name

    if not best_provider:
        raise RuntimeError("利用可能なプロバイダーがありません")

    return best_provider
```

---

## 🔄 処理フロー

### 基本的なリクエストフロー

```
ユーザー入力（prompt）
    ↓
LLMRequest作成
    ↓
プロバイダー選択
    │
    ├─ preferred_provider指定あり → 指定プロバイダー使用
    │
    └─ 自動選択
        ├─ 利用可能性チェック
        ├─ 設定状態チェック
        ├─ success_rate評価
        └─ 最適プロバイダー決定
    ↓
リクエスト実行
    ↓
応答受信（LLMResponse）
    ↓
履歴記録（DB保存）
    ↓
ユーザーに返却
```

### フォールバックフロー

```
ユーザー入力（prompt）
    ↓
provider_priority順に試行
    │
    ├─ Provider 1（例: Gemini）
    │   ├─ 状態チェック → OK
    │   ├─ リクエスト実行 → エラー（制限超過）
    │   └─ 次のプロバイダーへ
    │
    ├─ Provider 2（例: HuggingFace）
    │   ├─ 状態チェック → OK
    │   ├─ リクエスト実行 → 成功！
    │   └─ 応答返却
    │
    └─（全失敗の場合）RuntimeError
```

---

## 📦 依存モジュール

### プロバイダーモジュール

| モジュール | 役割 |
|-----------|------|
| `services/ai/provider_ollama.py` | Ollamaプロバイダー実装 |
| `services/ai/provider_gemini.py` | Geminiプロバイダー実装 |
| `services/ai/provider_huggingface.py` | HuggingFaceプロバイダー実装 |

### 共通モジュール

| モジュール | 役割 |
|-----------|------|
| `services/ai/llm_common.py` | 共通ユーティリティ、データクラス |
| `services/db/llm_history_manager.py` | LLM履歴管理 |
| `agents/common.py` | BaseAgent基底クラス |
| `agents/config_agent.py` | 設定管理 |

---

## 🧪 テストケース

### 単体テスト

```python
def test_llm_agent_initialization():
    """初期化テスト"""
    agent = LLMAgent()
    assert agent is not None
    assert len(agent.providers) > 0

def test_provider_selection():
    """プロバイダー選択テスト"""
    agent = LLMAgent()
    request = LLMRequest(prompt="テスト")
    provider = agent._select_provider(request)
    assert provider in agent.providers

def test_generate_response():
    """応答生成テスト"""
    agent = LLMAgent()
    response = agent.generate_response("こんにちは")
    assert isinstance(response, str)
    assert len(response) > 0

def test_fallback():
    """フォールバックテスト"""
    agent = LLMAgent()
    # 最初のプロバイダーを無効化
    agent.providers[agent.provider_priority[0]].available = False
    response = agent.generate_response_with_fallback("テスト")
    assert isinstance(response, str)
```

---

## 🔐 セキュリティ考慮事項

### API Key管理
- `.env`ファイルで管理（Git除外）
- 環境変数から読み込み
- ハードコーディング禁止

### プロンプトインジェクション対策
- システムメッセージとユーザープロンプトを分離
- 入力サニタイゼーション
- 出力バリデーション

### レート制限対策
- プロバイダー状態監視
- 自動フォールバック
- リクエストキューイング（将来実装）

---

*最終更新: 2025年11月2日*
