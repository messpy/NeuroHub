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

---

## 🎯 概要

### システム概要
NeuroHubは、AI エージェントとLLMサービスを統合するPythonベースのマルチエージェントシステムです。

### 設計原則
- **モジュラリティ**: 各コンポーネントの独立性
- **拡張性**: 新しいエージェント・サービスの追加容易性
- **Linux互換性**: Linux環境での最適化
- **標準化**: 統一されたインターフェース

---

## 🏗️ システムアーキテクチャ

```
NeuroHub Architecture
├── Agents Layer (agents/)
│   ├── CommandAgent       - システムコマンド実行
│   ├── ConfigAgent        - 設定管理
│   ├── GitAgent          - Git操作
│   └── LLMAgent          - LLM統合
├── Services Layer (services/)
│   ├── LLM Services       - AI/ML プロバイダー
│   ├── Database Services  - データ永続化
│   ├── Agent Services     - エージェント機能
│   └── MCP Services       - Model Context Protocol
└── Tools Layer (tools/)
    ├── Git Utilities      - Git支援ツール
    └── Core Utilities     - 基盤ユーティリティ
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

### LLMAgent インターフェース

```python
class LLMAgentInterface:
    """LLM統合エージェント"""

    def generate_response(self,
                         prompt: str,
                         model: str,
                         provider: str = "ollama",
                         max_tokens: int = 1000,
                         temperature: float = 0.7) -> LLMResponse:
        """LLM応答生成"""
        pass

    def get_available_models(self, provider: str) -> List[ModelInfo]:
        """利用可能モデル一覧"""
        pass

    def validate_provider(self, provider: str) -> bool:
        """プロバイダー検証"""
        pass
```

---

## 🔧 サービスインターフェース

### LLMプロバイダーインターフェース

```python
class LLMProviderInterface(ABC):
    """LLMプロバイダー基底インターフェース"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """テキスト生成"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """利用可能モデル取得"""
        pass

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

## 🔌 API仕様

### RESTful API エンドポイント

```python
# FastAPI ベースのAPI設計

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
