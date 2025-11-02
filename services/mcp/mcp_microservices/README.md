# MCPマイクロサービスアーキテクチャ

## 概要
MCPシステムをマイクロサービス化して、スケーラビリティと保守性を向上

## サービス構成

### 1. Gateway Service (api_gateway.py)
- すべてのリクエストの入口
- ルーティング
- 認証・認可
- レート制限

### 2. LLM Service (llm_service.py)
- LLM API統合
- プロバイダー管理
- 応答キャッシュ

### 3. Database Service (database_service.py)
- データベース操作
- トランザクション管理
- クエリ最適化

### 4. Analysis Service (analysis_service.py)
- ログ分析
- パフォーマンス分析
- レポート生成

### 5. Monitoring Service (monitoring_service.py)
- ヘルスチェック
- メトリクス収集
- アラート生成

## 実行方法

```bash
# すべてのサービスを起動
python services/mcp/mcp_microservices/start_all.py

# 個別サービス起動
python services/mcp/mcp_microservices/api_gateway.py
python services/mcp/mcp_microservices/llm_service.py
python services/mcp/mcp_microservices/database_service.py
python services/mcp/mcp_microservices/analysis_service.py
python services/mcp/mcp_microservices/monitoring_service.py
```

## アーキテクチャ図

```
┌─────────────────────┐
│   API Gateway       │  :8000
│   (ルーティング)     │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────┐
│  LLM   │   │Database│
│Service │   │Service │
│ :8001  │   │ :8002  │
└────────┘   └────────┘
    │             │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Analysis   │
    │  Service    │
    │   :8003     │
    └─────────────┘
           │
    ┌──────▼──────┐
    │ Monitoring  │
    │  Service    │
    │   :8004     │
    └─────────────┘
```

## 通信プロトコル
- HTTP/REST API
- JSON形式
- 非同期通信対応

## スケーリング戦略
- 水平スケーリング対応
- ロードバランサー統合
- サービス単位でのスケール

## 監視・ログ
- 各サービスの独立ログ
- 集約ログビューア
- メトリクス収集・可視化
