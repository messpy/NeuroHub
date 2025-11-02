# エージェント詳細仕様

[← プロジェクト概要に戻る](../PROJECT_OVERVIEW.md)

---

## 📂 agents/common.py - BaseAgentクラス

**機能**: 全エージェント共通の基底クラス

**設計方針**: 統一インターフェース、共通機能の集約

### クラス構造

```python
class BaseAgent(ABC):
    """全エージェント共通基底クラス"""

    def __init__(self, name: str, config_path: Optional[str] = None)
    def _setup_logging(self) -> logging.Logger
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]

    @abstractmethod
    def execute(self, prompt: str, **kwargs) -> Dict[str, Any]

    def handle_error(self, error: Exception, context: str) -> Dict[str, Any]
    def validate_input(self, input_data: str, min_length: int = 1) -> bool
```

---

### 主要メソッド

#### `__init__(name, config_path)`
**目的**: エージェント初期化

**処理**:
1. ロガー設定（`_setup_logging()`）
2. 設定ファイル読み込み（`_load_config()`）

**パラメータ**:
- `name`: エージェント名（ログファイル名に使用）
- `config_path`: 設定ファイルパス（省略時デフォルト）

**例**:
```python
class WeatherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="weather_agent", config_path="config/config.yaml")
```

---

#### `_setup_logging()`
**目的**: ロガー設定

**処理**:
1. ログディレクトリ作成（`logs/`）
2. ファイルハンドラー設定（`logs/{name}.log`）
3. コンソールハンドラー設定
4. フォーマット設定

**ログフォーマット**:
```
2024-12-01 10:30:45 - weather_agent - INFO - 天気情報を取得しました
```

**ログレベル**: INFO（デフォルト）

---

#### `_load_config(config_path)`
**目的**: 設定ファイル読み込み

**対応フォーマット**: YAML

**デフォルトパス**:
- `config/config.yaml`
- `config/agent_config.yaml`

**エラーハンドリング**:
- ファイル未存在 → 空辞書返却
- YAML構文エラー → 警告ログ、空辞書返却

**例**:
```python
config = self._load_config("config/config.yaml")
api_key = config.get('openweather', {}).get('api_key')
```

---

#### `execute(prompt, **kwargs)` (抽象メソッド)
**目的**: エージェント実行（サブクラスで実装必須）

**パラメータ**:
- `prompt`: ユーザー入力プロンプト
- `**kwargs`: 追加パラメータ

**戻り値**:
```python
{
    "success": bool,
    "result": Any,
    "error": Optional[str]
}
```

**実装例**:
```python
def execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
    try:
        result = self._perform_weather_lookup(prompt)
        return {
            "success": True,
            "result": result,
            "error": None
        }
    except Exception as e:
        return self.handle_error(e, f"execute: {prompt}")
```

---

#### `handle_error(error, context)`
**目的**: 統一エラーハンドリング

**処理**:
1. エラーログ記録
2. 標準化レスポンス生成

**戻り値**:
```python
{
    "success": False,
    "result": None,
    "error": str(error)
}
```

**例**:
```python
try:
    result = risky_operation()
except Exception as e:
    return self.handle_error(e, "risky_operation")
```

---

#### `validate_input(input_data, min_length)`
**目的**: 入力バリデーション

**チェック項目**:
- 非None
- 文字列型
- 最小長満たす

**パラメータ**:
- `input_data`: 検証対象
- `min_length`: 最小長（デフォルト: 1）

**戻り値**: `bool`

**例**:
```python
if not self.validate_input(prompt, min_length=3):
    return {
        "success": False,
        "result": None,
        "error": "入力が短すぎます"
    }
```

---

## 📂 agents/git_agent.py - Gitエージェント

**機能**: Git操作自動化

**継承**: `BaseAgent`

### 対応操作

1. **git status**
   - 変更ファイルリスト表示
   - ステージング状態表示

2. **git commit**
   - 自動コミットメッセージ生成（LLM使用）
   - ステージング→コミット

3. **git add**
   - ファイルステージング

4. **git push/pull**
   - リモート同期

---

### 使用例

```python
from agents.git_agent import GitAgent

agent = GitAgent()

# Git status
result = agent.execute("git status")
print(result["result"])

# 出力例:
# 変更されたファイル:
#   - modified: agents/common.py
#   - new file: docs/PROJECT_OVERVIEW.md
#   - modified: main.py
```

---

## 📂 agents/specialized/weather_agent.py - 天気エージェント

**機能**: 天気情報取得

**継承**: `BaseAgent`

### 主要機能

1. **位置検出**
   - IPベース位置推定
   - 都市名抽出

2. **天気情報取得**
   - OpenWeatherMap API
   - 気温、湿度、天気

3. **日本語変換**
   - weather_id → 日本語説明

---

### 使用例

```python
from agents.specialized.weather_agent import WeatherAgent

agent = WeatherAgent()

# 天気取得
result = agent.execute("今日の天気を教えて")

# 出力例:
# 東京の天気: 晴れ
# 気温: 18.5°C
# 湿度: 60%
```

---

### 設定 (config/config.yaml)

```yaml
openweather:
  api_key: YOUR_API_KEY
  default_city: Tokyo
```

---

## 📂 agents/specialized/web_agent.py - Web検索エージェント

**機能**: Web検索・スクレイピング

**継承**: `BaseAgent`

### 主要機能

1. **Google検索**
   - 検索クエリ実行
   - 上位10件取得

2. **Webスクレイピング**
   - HTML解析（BeautifulSoup）
   - テキスト抽出

3. **要約**
   - LLM使用（オプション）

---

### 使用例

```python
from agents.specialized.web_agent import WebAgent

agent = WebAgent()

# Web検索
result = agent.execute("PythonのAsyncIO チュートリアル")

# 出力例:
# 検索結果:
# 1. Python AsyncIO入門 - https://...
# 2. 非同期プログラミング完全ガイド - https://...
```

---

## 📂 agents/specialized/mcp_agent.py - MCPエージェント

**機能**: MCPプロジェクト生成

**継承**: `BaseAgent`

### 処理フロー

```
1. プロンプト受け取り
2. 設計書生成（LLM）
3. コード生成（LLM）
4. テスト生成（LLM）
5. デバッグ（auto_debugger）
6. プロジェクト出力
```

---

### 使用例

```python
from agents.specialized.mcp_agent import MCPAgent

agent = MCPAgent()

# プロジェクト生成
result = agent.execute("CSVをJSONに変換するCLIツール")

# 出力先:
# generated_projects/csv_json変換ツール_cli/
#   - main.py
#   - requirements.txt
#   - README.md
#   - tests/test_main.py
```

---

## 📂 agents/command_agent.py - コマンドエージェント

**機能**: シェルコマンド実行

**継承**: `BaseAgent`

### セキュリティ

**禁止コマンド**:
- `rm -rf`
- `sudo`
- `format`
- `dd`

**実行確認**: 危険コマンドは事前確認

---

### 使用例

```python
from agents.command_agent import CommandAgent

agent = CommandAgent()

# コマンド実行
result = agent.execute("ls -la")

# 出力例:
# total 120
# drwxr-xr-x  15 user user  4096 Dec  1 10:30 .
# ...
```

---

## 📂 agents/config_agent.py - 設定エージェント

**機能**: 設定ファイル管理

**継承**: `BaseAgent`

### 対応ファイル

- `config/config.yaml`
- `config/agent_config.yaml`
- `config/llm_config.yaml`
- `config/discord_config.yaml`

---

### 使用例

```python
from agents.config_agent import ConfigAgent

agent = ConfigAgent()

# 設定表示
result = agent.execute("LLM設定を表示")

# 出力例:
# LLM設定:
#   provider: ollama
#   model: qwen2.5:3b
#   temperature: 0.7
```

---

## 🔗 関連ドキュメント

- [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) - プロジェクト概要
- [MAIN_PY.md](./MAIN_PY.md) - main.py詳細仕様
- [SERVICES.md](./SERVICES.md) - サービス詳細仕様

---

[← プロジェクト概要に戻る](../PROJECT_OVERVIEW.md)
