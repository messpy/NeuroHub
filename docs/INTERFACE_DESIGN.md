# NeuroHub Interface Design Document (IF設計書)

## 📖 目次
1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [エージェントインターフェース](#エージェントインターフェース)
4. [サービスインターフェース](#サービスインターフェース)
5. [データフォーマット](#データフォーマット)
6. [API仕様](#api仕様)
7. [エラーハンドリング](#エラーハンドリング)
8. [セキュリティ](#セキュリティ)
9. [実装状況](#実装状況)

---

## 🎯 概要

### システム概要
NeuroHubは、AI エージェントとLLMサービスを統合するPythonベースのマルチエージェントシステムです。複数のLLMプロバイダー（Gemini、HuggingFace、Ollama）を統合し、Git操作の自動化とAI生成コミットメッセージの機能を提供します。

### 設計原則
- **モジュラリティ**: 各コンポーネントの独立性
- **拡張性**: 新しいエージェント・サービスの追加容易性
- **クロスプラットフォーム**: Windows/Linux環境での動作
- **標準化**: 統一されたインターフェース
- **フォールバック**: プロバイダー障害時の自動切り替え

### 主要機能（2025年11月現在）
- ✅ **Multi-LLM Integration**: 3つのLLMプロバイダーの統合管理
- ✅ **AI-Powered Git**: AI生成コミットメッセージとスマートGit操作
- ✅ **Provider Fallback**: プロバイダー障害時の自動フォールバック
- ✅ **Configuration Management**: YAML/環境変数ベースの設定管理
- ✅ **History Tracking**: LLM使用履歴とパフォーマンス統計
- ⚠️ **Command Execution**: システムコマンド実行（部分実装）

---

## 🏗️ システムアーキテクチャ

```
NeuroHub Architecture (実装済み)
├── Agents Layer (agents/)
│   ├── LLMAgent           - ✅ 3プロバイダー統合、フォールバック
│   ├── GitSmartAgent      - ✅ AI生成コミット、インタラクティブワークフロー
│   ├── CommandAgent       - ⚠️ 基本実装済み（テスト要調整）
│   ├── ConfigAgent        - ✅ YAML設定管理
│   └── GitAgent          - ✅ 基本Git操作
├── Services Layer (services/)
│   ├── LLM Services       - ✅ Gemini/HuggingFace/Ollama
│   │   ├── provider_gemini.py      - ✅ Gemini API統合
│   │   ├── provider_huggingface.py - ✅ HF Router統合
│   │   ├── provider_ollama.py      - ✅ Ollama統合＋自動起動
│   │   └── llm_common.py          - ✅ 共通ユーティリティ
│   ├── Database Services  - ✅ SQLite + FTS5検索
│   │   └── llm_history_manager.py - ✅ 履歴・統計管理
│   ├── Agent Services     - ✅ エージェント支援機能
│   └── MCP Services       - ⚠️ 計画段階
└── Tools Layer (tools/)
    ├── Git Utilities      - ✅ git_commit_ai, git_helper
    ├── Project Organizer  - ✅ ファイル整理ツール
    └── Core Utilities     - ✅ bs_core, weather_core
```

---

## 🤖 エージェントインターフェース

### 基底エージェントクラス

```python
class BaseAgent(ABC):
    """全エージェントの基底クラス"""

    @abstractmethod
    def execute(self, command: str, **kwargs) -> AgentResponse:
        """エージェント実行インターフェース"""
        pass

    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """入力検証インターフェース"""
        pass

    @abstractmethod
    def get_status(self) -> AgentStatus:
        """ステータス取得インターフェース"""
        pass
```

### CommandAgent インターフェース

```python
class CommandAgentInterface:
    """システムコマンド実行エージェント"""

    def execute_command(self,
                       command: str,
                       cwd: Optional[str] = None,
                       timeout: int = 30,
                       capture_output: bool = True) -> CommandResult:
        """
        Linuxコマンド実行

        Args:
            command: 実行するLinuxコマンド
            cwd: 作業ディレクトリ (Linux path)
            timeout: タイムアウト秒数
            capture_output: 出力キャプチャフラグ

        Returns:
            CommandResult: 実行結果

        Raises:
            CommandExecutionError: コマンド実行エラー
            TimeoutError: タイムアウトエラー
        """
        pass

    def validate_command(self, command: str) -> ValidationResult:
        """Linuxコマンドの安全性検証"""
        pass

    def get_command_history(self) -> List[CommandHistory]:
        """コマンド実行履歴取得"""
        pass
```

### GitAgent インターフェース

```python
class GitAgentInterface:
    """Git操作エージェント (Linux環境最適化)"""

    def init_repository(self, path: str) -> GitResult:
        """Gitリポジトリ初期化 (Linux権限考慮)"""
        pass

    def commit_changes(self,
                      message: str,
                      files: Optional[List[str]] = None,
                      author: Optional[str] = None) -> GitResult:
        """変更のコミット"""
        pass

    def get_status(self) -> GitStatus:
        """Gitステータス取得"""
        pass

    def create_branch(self, branch_name: str) -> GitResult:
        """ブランチ作成"""
        pass

    def merge_branch(self, branch_name: str) -> GitResult:
        """ブランチマージ"""
        pass
```

### LLMAgent インターフェース（実装済み）

```python
class LLMAgentInterface:
    """LLM統合エージェント - 2025年11月実装版"""

    def __init__(self, config_path: str = None):
        """
        LLMAgent初期化

        Args:
            config_path: 設定ファイルパス（オプション）
        """
        pass

    def check_provider_status(self, force_refresh: bool = False) -> Dict[str, ProviderStatus]:
        """
        プロバイダー状態確認

        Args:
            force_refresh: 強制更新フラグ

        Returns:
            Dict[str, ProviderStatus]: プロバイダー状態辞書
            - "gemini": Gemini API状態
            - "huggingface": HuggingFace Router状態
            - "ollama": Ollama状態
        """
        pass

    def get_best_provider(self, request_type: str = "general") -> Optional[str]:
        """
        最適プロバイダー選択

        Args:
            request_type: リクエストタイプ（将来拡張用）

        Returns:
            Optional[str]: 最適プロバイダー名またはNone
        """
        pass

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        テキスト生成（フォールバック対応）

        Args:
            request: LLMRequest オブジェクト

        Returns:
            LLMResponse: 統一レスポンス形式
        """
        pass

    def generate_commit_message(self,
                               file_path: str,
                               diff_content: str,
                               commit_type: str = "auto") -> str:
        """
        Git コミットメッセージ生成

        Args:
            file_path: ファイルパス
            diff_content: 差分内容
            commit_type: コミットタイプ

        Returns:
            str: 生成されたコミットメッセージ
        """
        pass

    def get_status_report(self) -> Dict[str, Any]:
        """
        システム状態レポート取得

        Returns:
            Dict[str, Any]: プロバイダー状態、統計情報等
        """
        pass
```

### LLMRequest データクラス（実装済み）

```python
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
```

### ProviderStatus データクラス（実装済み）

```python
@dataclass
class ProviderStatus:
    """プロバイダー状態"""
    name: str                           # プロバイダー名
    available: bool                     # 利用可能フラグ
    configured: bool                    # 設定済みフラグ
    last_response_time: Optional[float] # 最終レスポンス時間
    success_rate: float = 0.0          # 成功率
    error_message: Optional[str] = None # エラーメッセージ
```

---

## 🔧 サービスインターフェース

### LLMプロバイダーインターフェース（実装済み）

```python
class LLMProviderInterface:
    """LLMプロバイダー統一インターフェース - 実装版"""

    def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功可否
        """
        pass

    def infer(self, prompt: str, opts: Dict[str, Any] = None) -> LLMResponse:
        """
        推論実行（プロバイダー固有実装）

        Args:
            prompt: 入力プロンプト
            opts: プロバイダー固有オプション

        Returns:
            LLMResponse: 統一レスポンス形式
        """
        pass
```

### Gemini Provider（実装済み）

```python
class GeminiConfig:
    """Google Gemini API プロバイダー"""

    def test_connection(self) -> bool:
        """Gemini API接続テスト"""
        pass

    def infer(self, prompt: str, opts: Dict[str, Any] = None) -> LLMResponse:
        """
        Gemini推論実行

        対応オプション:
        - temperature: 0.0-1.0
        - max_tokens: 最大トークン数
        - system_message: システムメッセージ
        """
        pass
```

### HuggingFace Provider（実装済み）

```python
class HuggingFaceConfig:
    """HuggingFace Router プロバイダー"""

    def test_connection(self) -> bool:
        """HF Router接続テスト"""
        pass

    def infer(self, prompt: str, opts: Dict[str, Any] = None, system_text: str = None) -> LLMResponse:
        """
        HuggingFace推論実行

        対応オプション:
        - model: モデル指定
        - max_tokens: 最大トークン数
        - temperature: 温度設定
        """
        pass
```

### Ollama Provider（実装済み）

```python
class OllamaConfig:
    """Ollama ローカルLLM プロバイダー"""

    def test_connection(self) -> bool:
        """Ollama接続テスト＋自動起動"""
        pass

    def infer(self, prompt: str) -> LLMResponse:
        """
        Ollama推論実行

        特徴:
        - 自動サーバー起動
        - 複数モデル対応
        - ローカル実行
        """
        pass

    def start_ollama_server(self) -> bool:
        """Ollamaサーバー自動起動"""
        pass
```

    @abstractmethod
    def validate_connection(self) -> bool:
        """接続検証"""
        pass

class OllamaProvider(LLMProviderInterface):
    """Ollama プロバイダー (Linux最適化)"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session = requests.Session()

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Ollama経由でのテキスト生成"""
        pass

class GeminiProvider(LLMProviderInterface):
    """Google Gemini プロバイダー"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Gemini経由でのテキスト生成"""
        pass
```

### データベースサービスインターフェース

```python
class DatabaseServiceInterface(ABC):
    """データベースサービス基底インターフェース"""

    @abstractmethod
    def connect(self) -> bool:
        """データベース接続"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: List[Any]) -> QueryResult:
        """クエリ実行"""
        pass

    @abstractmethod
    def close(self) -> None:
        """接続クローズ"""
        pass

class SQLiteService(DatabaseServiceInterface):
    """SQLite データベースサービス (Linux ファイル権限対応)"""

    def __init__(self, db_path: str = "/var/lib/neurohub/data.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self) -> bool:
        """SQLite接続 (Linux権限チェック付き)"""
        if not os.access(os.path.dirname(self.db_path), os.W_OK):
            raise PermissionError(f"No write permission: {self.db_path}")
        pass
```

---

## 📊 データフォーマット

### 共通レスポンス形式

```python
@dataclass
class BaseResponse:
    """基底レスポンスクラス"""
    success: bool
    message: str
    timestamp: datetime
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResponse(BaseResponse):
    """エージェントレスポンス"""
    agent_type: str
    result: Any
    error_code: Optional[str] = None

@dataclass
class CommandResult(BaseResponse):
    """コマンド実行結果"""
    command: str
    return_code: int
    stdout: str
    stderr: str
    cwd: str
    environment: Dict[str, str]

@dataclass
class GitResult(BaseResponse):
    """Git操作結果"""
    operation: str
    repository_path: str
    branch: str
    commit_hash: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)

@dataclass
class LLMResponse(BaseResponse):
    """LLM応答結果"""
    model: str
    provider: str
    prompt: str
    response_text: str
    tokens_used: int
    cost: Optional[float] = None
```

### 設定データ形式

```yaml
# config.yaml - Linux環境設定
system:
  platform: "linux"
  shell: "/bin/bash"
  encoding: "utf-8"

agents:
  command_agent:
    enabled: true
    timeout: 30
    safe_commands_only: true
    allowed_directories: ["/home/user", "/tmp"]

  git_agent:
    enabled: true
    default_branch: "main"
    auto_commit: false
    user_name: "NeuroHub Agent"
    user_email: "agent@neurohub.local"

  llm_agent:
    enabled: true
    default_provider: "ollama"
    max_tokens: 1000
    temperature: 0.7

services:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 60
    models_path: "/home/user/.ollama/models"

  gemini:
    api_key_env: "GEMINI_API_KEY"
    model: "gemini-1.5-flash"

  database:
    type: "sqlite"
    path: "/var/lib/neurohub/neurohub.db"
    backup_path: "/var/lib/neurohub/backups/"
```

---

## � 実装状況（2025年11月1日現在）

### ✅ 完全実装済み

#### LLM統合システム
- **LLMAgent**: 3プロバイダー統合管理
- **Provider Fallback**: 自動フォールバック機能
- **Response Parsing**: 統一レスポンス形式
- **Connection Testing**: プロバイダー接続確認

#### プロバイダー実装
- **Gemini API**: Google Gemini 2.5 Flash対応
- **HuggingFace Router**: OpenAI互換API経由
- **Ollama**: ローカルLLM + 自動サーバー管理

#### Git統合
- **GitSmartAgent**: AIコミットメッセージ生成
- **Interactive Workflow**: ファイル分類・選択UI
- **git_commit_ai**: コマンドラインツール

#### データ管理
- **LLMHistoryManager**: SQLite + FTS5検索
- **Provider Statistics**: パフォーマンス統計
- **Configuration**: YAML + 環境変数

### ⚠️ 部分実装

#### コマンド実行
- **CommandAgent**: 基本実装済み（テスト要調整）
- **Safety Validation**: 計画段階

#### その他エージェント
- **ConfigAgent**: 基本機能実装済み
- **GitAgent**: 基本Git操作対応

### 🚧 計画段階

#### MCP統合
- **Model Context Protocol**: 設計段階
- **外部サービス連携**: 検討中

#### REST API
- **FastAPI**: 計画段階
- **WebUI**: 将来機能

### 🧪 テスト状況

#### 統合テスト: ✅ PASS
- LLMAgent統合: 5/5 プロバイダーテスト成功
- プロバイダー個別: 3/3 すべて動作確認済み
- Git機能: 基本動作確認済み

#### 単体テスト: ⚠️ 部分実装
- LLMAgent: 完全テスト作成済み
- プロバイダー: 動作テスト完了
- CommandAgent: インターフェース調整要

### 📈 パフォーマンス（実測値）

#### レスポンス時間
- **Gemini**: ~1.0秒（安定）
- **HuggingFace**: ~0.3秒（高速）
- **Ollama**: ~1.6秒（ローカル・モデル依存）

#### 成功率
- **全プロバイダー**: 接続テスト100%成功
- **フォールバック**: 正常動作確認済み
- **AI生成コミット**: 実用レベル

### 🔧 設定状況

#### 環境変数（必須）
```bash
# .env ファイル設定済み
GEMINI_API_KEY=***
HUGGINGFACE_API_KEY=***
OLLAMA_BASE_URL=http://localhost:11434
```

#### 設定ファイル
- `config/config.yaml`: ✅ 構成済み
- `config/llm_config.yaml`: ✅ プロバイダー設定済み
- `config/prompt_templates.yaml`: ✅ テンプレート準備済み

---

## �🔌 API仕様（計画）

### RESTful API エンドポイント

```python
# FastAPI ベースのAPI設計（将来実装）

@app.post("/api/v1/agents/command/execute")
async def execute_command(request: CommandRequest) -> CommandResult:
    """コマンド実行API"""
    pass

@app.get("/api/v1/agents/git/status")
async def get_git_status(repo_path: str) -> GitStatus:
    """Gitステータス取得API"""
    pass

@app.post("/api/v1/services/llm/generate")
async def generate_text(request: LLMRequest) -> LLMResponse:
    """LLMテキスト生成API"""
    pass

@app.get("/api/v1/system/health")
async def health_check() -> HealthStatus:
    """ヘルスチェックAPI"""
    pass
```

### WebSocket API

```python
@app.websocket("/ws/agents/realtime")
async def websocket_agent_updates(websocket: WebSocket):
    """リアルタイムエージェント状態更新"""
    await websocket.accept()
    while True:
        # エージェント状態をリアルタイム配信
        pass
```

---

## ⚠️ エラーハンドリング

### エラー階層

```python
class NeuroHubError(Exception):
    """NeuroHub基底例外"""
    pass

class AgentError(NeuroHubError):
    """エージェント関連エラー"""
    pass

class CommandExecutionError(AgentError):
    """コマンド実行エラー"""
    def __init__(self, command: str, return_code: int, stderr: str):
        self.command = command
        self.return_code = return_code
        self.stderr = stderr
        super().__init__(f"Command failed: {command} (code: {return_code})")

class GitOperationError(AgentError):
    """Git操作エラー"""
    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Git {operation} failed: {details}")

class LLMProviderError(NeuroHubError):
    """LLMプロバイダーエラー"""
    pass

class ConfigurationError(NeuroHubError):
    """設定エラー"""
    pass
```

### Linux固有エラー処理

```python
def handle_linux_permissions(func):
    """Linux権限エラーデコレータ"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PermissionError as e:
            if e.errno == 13:  # Permission denied
                raise ConfigurationError(
                    f"Insufficient permissions. Try: sudo chmod +x {e.filename}"
                )
            raise
        except FileNotFoundError as e:
            if "command not found" in str(e):
                raise ConfigurationError(
                    f"Command not installed. Try: sudo apt-get install {e.filename}"
                )
            raise
    return wrapper
```

---

## 🔒 セキュリティ

### 認証・認可

```python
class SecurityManager:
    """セキュリティ管理"""

    def validate_command(self, command: str, user: str) -> bool:
        """コマンド実行権限検証"""
        # 危険なコマンドのブラックリスト
        dangerous_commands = ['rm -rf', 'sudo', 'chmod 777', '> /dev/']
        return not any(cmd in command for cmd in dangerous_commands)

    def validate_file_access(self, path: str, mode: str = 'r') -> bool:
        """ファイルアクセス権限検証 (Linux)"""
        abs_path = os.path.abspath(path)
        if mode == 'w' and not os.access(os.path.dirname(abs_path), os.W_OK):
            return False
        return os.access(abs_path, os.R_OK if 'r' in mode else os.W_OK)
```

### データ暗号化

```python
class EncryptionService:
    """データ暗号化サービス"""

    def encrypt_api_key(self, api_key: str) -> str:
        """APIキー暗号化 (Linux keyring使用)"""
        pass

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """APIキー復号化"""
        pass
```

---

## 📋 実装チェックリスト

### 🤖 エージェント実装
- [ ] BaseAgent抽象クラス実装
- [ ] CommandAgent Linux最適化
- [ ] GitAgent Linux権限対応
- [ ] LLMAgent プロバイダー統合
- [ ] ConfigAgent YAML/JSON対応

### 🔧 サービス実装
- [ ] OllamaProvider Linux対応
- [ ] GeminiProvider API統合
- [ ] HuggingFaceProvider 実装
- [ ] SQLiteService Linux権限管理
- [ ] MCP Service 実装

### 📊 データ層実装
- [ ] BaseResponse 標準化
- [ ] エラーレスポンス統一
- [ ] ログフォーマット統一
- [ ] 設定スキーマ検証

### 🔌 API実装
- [ ] FastAPI セットアップ
- [ ] RESTful エンドポイント
- [ ] WebSocket リアルタイム通信
- [ ] OpenAPI ドキュメント生成

### ⚠️ エラーハンドリング
- [ ] 例外階層定義
- [ ] Linux固有エラー処理
- [ ] ログ統合
- [ ] 復旧メカニズム

### 🔒 セキュリティ
- [ ] コマンド検証機能
- [ ] ファイルアクセス制限
- [ ] API認証実装
- [ ] 暗号化サービス

### 🧪 テスト
- [ ] 単体テスト完全カバレッジ
- [ ] 統合テスト実装
- [ ] Linux環境テスト
- [ ] セキュリティテスト

---

## 📚 関連ドキュメント

- [README.md](./README.md) - プロジェクト概要
- [TESTING.md](./docs/TESTING.md) - テスト戦略
- [LINUX_TEST_REPORT.md](./LINUX_TEST_REPORT.md) - Linux テスト結果
- [API_REFERENCE.md](./docs/API_REFERENCE.md) - API リファレンス

---

*最終更新: 2025年11月1日*
*Linux環境での運用を前提とした設計仕様*
