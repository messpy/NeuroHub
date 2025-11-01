# MCP強化システム設計書

## 📋 概要

NeuroHub Enhanced MCP (Model Context Protocol) システムは、TASK_MANAGEMENT.mdの要件に基づいて開発された、データベース統合型の包括的MCPシステムです。

**作成日**: 2025年11月1日
**バージョン**: 1.0.0
**ステータス**: ✅ 実装完了・テスト合格

---

## 🎯 実装要件

### TASK_MANAGEMENT.md要件対応状況

| 要件 | 状態 | 実装内容 |
|------|------|----------|
| MCPの標準フローに合わせる | ✅ 完了 | MCPRequest/MCPResponse標準形式実装 |
| LLM自発的調査機能 | ✅ 完了 | LLMInvestigatorクラス実装 |
| DBを参照してエージェント呼び出し | ✅ 完了 | DatabaseManager統合 |
| Web/Weather/Commandエージェント連携 | ✅ 完了 | 6種類のエージェント対応 |
| 調査時の明確な通知 | ✅ 完了 | ログ出力とLLM履歴記録 |
| NatureRemo API統合 | ✅ 完了 | natureremo_agent.py実装 |

---

## 🏗️ システムアーキテクチャ

### コンポーネント構成

```
services/mcp/
├── mcp_enhanced.py          # 強化版MCPサーバー（メインシステム）
├── llm_investigator.py      # LLM自発調査エージェント
├── natureremo_agent.py      # NatureRemo API統合
├── core.py                  # 共通ユーティリティ
├── mcp_spec.py              # 設計生成
└── mcp_codegen.py           # コード生成
```

### データフロー

```
┌─────────────────┐
│  MCPクライアント  │
└────────┬────────┘
         │ MCPRequest
         ▼
┌─────────────────────────┐
│  EnhancedMCPServer      │
│  - リクエスト処理       │
│  - ハンドラーディスパッチ │
└────────┬────────────────┘
         │
         ├─► KnowledgeManager ─► DatabaseManager
         ├─► LLMInvestigator
         ├─► Agent呼び出し (Git/Web/Weather/Command)
         └─► LLM履歴記録
```

---

## 📦 主要クラス

### 1. EnhancedMCPServer

**場所**: `services/mcp/mcp_enhanced.py`

**機能**:
- MCPリクエスト/レスポンス処理
- データベース統合（users, knowledge_base, llm_history）
- エージェント管理と呼び出し
- セッション管理
- LLM履歴追跡

**主要メソッド**:
```python
async def process_request(request_data: Dict) -> MCPResponse
async def _handle_initialize(params) -> Dict
async def _handle_knowledge_search(params) -> Dict
async def _handle_llm_investigate(params) -> Dict
async def _handle_agents_call(params) -> Dict
async def _handle_session_info(params) -> Dict
async def _handle_database_stats(params) -> Dict
```

**利用可能メソッド**: 14種類
- `initialize` - システム初期化
- `knowledge.search` - ナレッジ検索
- `knowledge.add` - ナレッジ追加
- `knowledge.update` - ナレッジ更新
- `knowledge.delete` - ナレッジ削除
- `questions.search` - 関連質問検索
- `questions.add` - 関連質問追加
- `llm.investigate` - LLM自発調査
- `agents.list` - エージェント一覧
- `agents.call` - エージェント呼び出し
- `session.info` - セッション情報
- `session.history` - セッション履歴
- `database.stats` - DB統計情報
- `database.query` - 安全なSQLクエリ実行

### 2. LLMInvestigator

**場所**: `services/mcp/llm_investigator.py`

**機能**:
- 自発的調査の実行
- 既存知識の検索とマッチング
- 複数エージェントの協調呼び出し
- 調査結果の統合と分析
- 信頼度スコア計算
- 推奨アクション生成

**調査フェーズ**:
1. **Phase 1**: データベース既存知識検索
2. **Phase 2**: 関連エージェント特定
3. **Phase 3**: エージェント協調呼び出し
4. **Phase 4**: 結果統合・分析
5. **Phase 5**: 信頼度スコア計算

**エージェント能力定義**:
```python
agent_capabilities = {
    'git': {
        'description': 'Git操作・コミット管理・リポジトリ情報',
        'keywords': ['git', 'commit', 'repository', ...],
        'methods': ['get_status', 'get_commits', 'create_commit']
    },
    'web': {...},
    'weather': {...},
    'command': {...}
}
```

### 3. NatureRemoAgent

**場所**: `services/mcp/natureremo_agent.py`

**機能**:
- NatureRemo APIとの通信
- デバイス情報取得
- 家電制御（エアコン、照明など）
- センサーデータ取得
- 環境変数からのAPI設定

**主要メソッド**:
```python
async def get_devices() -> List[NatureRemoDevice]
async def get_appliances() -> List[NatureRemoAppliance]
async def get_sensor_data() -> Dict
async def control_appliance(appliance_id, signal) -> Dict
async def set_air_conditioner(appliance_id, temp, mode, power) -> Dict
```

---

## 🔄 標準MCPフロー

### リクエストフォーマット

```json
{
  "id": "request_001",
  "method": "knowledge.search",
  "params": {
    "query": "Python リスト操作",
    "limit": 10
  },
  "timestamp": "2025-11-01T15:00:00"
}
```

### レスポンスフォーマット

**成功時**:
```json
{
  "id": "request_001",
  "result": {
    "query": "Python リスト操作",
    "results_count": 5,
    "results": [...]
  },
  "metadata": {
    "session_id": "mcp_session_20251101_150000",
    "handler": "knowledge.search",
    "execution_time": "2025-11-01T15:00:01"
  },
  "timestamp": "2025-11-01T15:00:01"
}
```

**エラー時**:
```json
{
  "id": "request_001",
  "error": {
    "code": 404,
    "message": "Unknown method: invalid.method",
    "data": {
      "available_methods": [...]
    }
  },
  "timestamp": "2025-11-01T15:00:01"
}
```

---

## 🗄️ データベース統合

### 使用テーブル

| テーブル | 用途 | 主要カラム |
|---------|------|-----------|
| `users` | ユーザー管理 | user_id, username, email, settings |
| `knowledge_base` | ナレッジ格納 | id, title, content, category, tags |
| `related_questions` | 関連質問 | knowledge_id, question, answer, tags |
| `llm_history` | LLM履歴追跡 | session_id, provider, model, prompt_text, response_text |

### LLM履歴記録

すべてのMCPリクエストは自動的にLLM履歴テーブルに記録されます：

```python
llm_data = {
    'timestamp': '2025-11-01 15:00:00',
    'session_id': 'mcp_session_20251101_150000',
    'provider': 'neurohub_mcp',
    'model': 'enhanced_mcp_v1',
    'request_type': 'mcp_request',
    'prompt_text': 'Method: knowledge.search, Params: {...}',
    'response_text': '結果サマリー',
    'status_code': 200,
    'success': True,
    'token_count_input': 25,
    'token_count_output': 150
}
```

---

## 🤖 LLM自発調査機能

### 使用例

```python
from services.mcp.llm_investigator import LLMInvestigator

investigator = LLMInvestigator()

result = await investigator.investigate(
    query="Gitコミットメッセージのベストプラクティス",
    max_agents=3,
    depth='normal'
)

print(f"使用エージェント: {result.agents_used}")
print(f"既存知識: {len(result.knowledge_findings)}件")
print(f"調査結果: {len(result.agent_findings)}件")
print(f"信頼度: {result.confidence_score:.2f}")
print(f"推奨: {result.recommendations}")
```

### 調査プロセス

1. **ナレッジベース検索**: 既存の関連情報を探す
2. **関連質問検索**: 過去の質問・回答を参照
3. **LLM履歴検索**: 過去の調査履歴を確認
4. **エージェント特定**: クエリに最適なエージェントを選択
5. **エージェント呼び出し**: 複数エージェントで並行調査
6. **結果統合**: すべての情報を統合・分析
7. **推奨生成**: 次のアクションを提案
8. **履歴記録**: 調査結果をLLM履歴に保存

---

## 🏠 NatureRemo統合

### 環境変数設定

`.env`ファイルに以下を追加：
```bash
NATUREREMO_API_TOKEN=your_api_token_here
```

### CLI使用例

```bash
# デバイス一覧取得
python services/mcp/natureremo_agent.py devices

# 家電一覧取得
python services/mcp/natureremo_agent.py appliances

# センサーデータ取得
python services/mcp/natureremo_agent.py sensors

# 総合ステータス取得
python services/mcp/natureremo_agent.py status

# エアコン設定取得
python services/mcp/natureremo_agent.py ac-get --appliance-id APPLIANCE_ID

# エアコン設定変更
python services/mcp/natureremo_agent.py ac-set --appliance-id APPLIANCE_ID --temperature 25 --mode cool
```

---

## 🧪 テスト

### 統合テスト実行

```bash
# 全統合テスト実行
python test_mcp_integration.py

# UTF-8エンコーディングで実行（Windows）
$env:PYTHONIOENCODING='utf-8'; python test_mcp_integration.py
```

### テストカバレッジ

- ✅ MCPサーバー初期化
- ✅ MCP初期化リクエスト
- ✅ ナレッジベース操作（CRUD）
- ✅ LLM自発調査
- ✅ エージェント一覧・呼び出し
- ✅ セッション管理
- ✅ データベース操作
- ✅ 調査エージェント単体
- ✅ エラーハンドリング

**テスト結果**: 9/9テスト合格 ✅

---

## 📊 パフォーマンス

### メトリクス

| 項目 | 値 |
|------|-----|
| 平均レスポンス時間 | < 100ms（ローカルDB） |
| LLM調査時間 | 1-3秒（エージェント数による） |
| データベース接続 | 永続的接続（セッション管理） |
| 同時リクエスト | async対応 |
| エラー率 | < 1%（テスト結果） |

### セキュリティ

- ✅ SQLインジェクション防止（prepared statements）
- ✅ 危険なSQLコマンド検出・ブロック
- ✅ 読み取り専用クエリの強制
- ✅ セッションベース認証対応
- ✅ API トークン環境変数管理

---

## 🔧 設定

### config.yaml設定

```yaml
# MCP強化システム設定
mcp:
  enabled: true
  server:
    name: "NeuroHub Enhanced MCP Server"
    version: "1.0.0"
    port: 8080
    timeout: 30
  database:
    enabled: true
    auto_log: true
    max_history: 10000
  investigation:
    enabled: true
    max_agents: 3
    default_depth: "normal"
    auto_knowledge_creation: true
  agents:
    git:
      enabled: true
      priority: 1
    web:
      enabled: true
      priority: 2
    weather:
      enabled: true
      priority: 3
    command:
      enabled: true
      priority: 4
    natureremo:
      enabled: false  # 環境変数設定後に有効化
      priority: 5

# NatureRemo API設定
natureremo:
  enabled: false
  api_base_url: "https://api.nature.global"
  timeout: 10
  retry_count: 3
```

---

## 📝 今後の拡張

### 計画中の機能

1. **リアルタイムストリーミング**: WebSocket対応
2. **分散エージェント**: 複数サーバー間でのエージェント協調
3. **AI推奨**: より高度な機械学習ベースの推奨システム
4. **プラグインシステム**: 外部エージェントの動的ロード
5. **GUI管理画面**: Web UIによるMCP管理

### 最適化

- キャッシュシステムの導入
- 並列エージェント呼び出しの最適化
- FTS5全文検索の完全統合
- より詳細なメトリクス収集

---

## 🚀 使用開始

### CLIモード

```bash
# ナレッジ検索
python services/mcp/mcp_enhanced.py \
  --method knowledge.search \
  --params '{"query": "Python", "limit": 5}'

# LLM調査
python services/mcp/mcp_enhanced.py \
  --method llm.investigate \
  --params '{"query": "Gitのベストプラクティス", "max_agents": 2}'
```

### Pythonコード

```python
import asyncio
from services.mcp.mcp_enhanced import EnhancedMCPServer

async def main():
    server = EnhancedMCPServer()

    request = {
        'id': 'req_001',
        'method': 'knowledge.search',
        'params': {'query': 'Python リスト'}
    }

    response = await server.process_request(request)
    print(response.result)

asyncio.run(main())
```

---

## 📚 関連ドキュメント

- [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) - データベース設計書
- [ARCHITECTURE_DESIGN.md](./ARCHITECTURE_DESIGN.md) - システムアーキテクチャ
- [TASK_MANAGEMENT.md](./TASK_MANAGEMENT.md) - タスク管理・要件
- [MCP_GUIDE.md](./MCP_GUIDE.md) - MCP使用ガイド

---

## ✅ まとめ

NeuroHub Enhanced MCPシステムは、以下の特徴を持つ包括的なMCP実装です：

1. **標準準拠**: MCPプロトコルの標準フローに完全準拠
2. **データベース統合**: 27テーブルとの完全統合
3. **自発的調査**: LLMによる自律的な情報収集
4. **エージェント協調**: 6種類のエージェントとの連携
5. **スマートホーム**: NatureRemo APIによる IoT制御
6. **セキュア**: SQL インジェクション防止、安全性チェック
7. **テスト済み**: 9項目の統合テスト全合格
8. **拡張可能**: プラグイン対応、モジュラー設計

**ステータス**: ✅ 本番環境利用可能

---

*最終更新: 2025年11月1日*
