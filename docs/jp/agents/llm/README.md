# LLMエージェント 概要

## 🎯 役割と責任

LLMエージェント（`agents/llm_agent.py`）は、複数のLLM（Large Language Model）プロバイダーを統合管理し、NeuroHub全体にAI機能を提供する中核的なエージェントです。

---

## 📋 主要機能

### 1. プロバイダー統合管理
- **Ollama**: ローカルLLM実行環境
- **Gemini**: Google AI API
- **HuggingFace**: Groq経由のInference API

### 2. 自動フォールバック
プロバイダーのエラー・制限時に自動的に別プロバイダーに切り替え

### 3. モデル管理
- モデル一覧取得
- 自動モデル選択
- カスタムモデル（Modelfile）のビルド

### 4. テキスト処理
- 日本語対応の安全な文字数制限
- チャンク処理（長文分割）
- システムプロンプト管理

---

## 🏗️ アーキテクチャ

```
┌────────────────────────────────────────┐
│        LLM Agent (llm_agent.py)        │
│                                        │
│  - プロバイダー選択                     │
│  - リクエスト管理                       │
│  - エラーハンドリング                   │
│  - フォールバック制御                   │
└────────────┬───────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼───┐ ┌─▼───┐ ┌─▼────────┐
│Ollama │ │Gemini│ │HuggingFace│
│Provider│ │Provider│ │Provider  │
└────────┘ └──────┘ └──────────┘
    │        │        │
┌───▼────────▼────────▼───┐
│   LLM Common Module      │
│  (services/ai/           │
│   llm_common.py)         │
└──────────────────────────┘
```

---

## 🔧 使用方法

### 基本的な使用例

```python
from agents.llm_agent import LLMAgent

# エージェント初期化
agent = LLMAgent()

# プロンプト送信（自動プロバイダー選択）
response = agent.generate_response("こんにちは")
print(response)
# 出力例: "こんにちは！お元気ですか？..."

# 特定プロバイダー指定
response = agent.generate_response(
    "Pythonのコードを書いて",
    provider="ollama"
)
```

### プロバイダー切り替え例

```python
# プロバイダー優先順位指定
agent.set_provider_priority(["gemini", "huggingface", "ollama"])

# 自動フォールバック（Geminiエラー時→HuggingFace→Ollama）
response = agent.generate_response_with_fallback("質問内容")
```

### モデル管理

```python
# 利用可能モデル一覧取得
models = agent.list_models(provider="ollama")
print(models)
# 出力: ["qwen2.5:0.5b-instruct", "llama2", ...]

# モデル変更
agent.switch_model(provider="ollama", model="llama2")
```

---

## 📊 対応プロバイダー詳細

### 1. Ollama
- **特徴**: ローカル実行、無制限、オフライン可
- **推奨モデル**: `qwen2.5:0.5b-instruct`（軽量・高速）
- **設定場所**: `config/llm_config.yaml`
- **セットアップ**: `ollama pull qwen2.5:0.5b-instruct`

### 2. Gemini
- **特徴**: 高品質、高速、日本語対応優秀
- **制限**: 1日250リクエスト（無料プラン）
- **推奨モデル**: `gemini-2.5-flash`
- **API Key**: `.env`の`GEMINI_API_KEY`

### 3. HuggingFace（Groq経由）
- **特徴**: 高速推論、多様なモデル
- **推奨モデル**: `openai/gpt-oss-20b:groq`
- **API Key**: `.env`の`HUGGINGFACE_API_KEY`
- **エンドポイント**: Groq Inference API

---

## 🧪 テスト

### テストファイル
- `test_hello_llm.py`: 基本動作確認（3プロバイダー）
- `tests/test_provider_ollama.py`: Ollama詳細テスト
- `tests/test_provider_gemini.py`: Gemini詳細テスト
- `tests/test_provider_huggingface.py`: HuggingFace詳細テスト

### 実行コマンド

```bash
# 全プロバイダー動作確認
python3 test_hello_llm.py

# Ollamaテスト（9テスト）
pytest tests/test_provider_ollama.py -v

# 統合テスト
pytest tests/ -k llm -v
```

---

## 📖 関連ドキュメント

- [詳細設計](./DETAILED_DESIGN.md) - 内部構造、クラス設計
- [プロバイダー設計](./PROVIDER_DESIGN.md) - 各プロバイダー仕様
- [その他設計](./OTHER_DESIGNS.md) - 拡張機能、カスタマイズ

---

## 🔗 依存関係

### 直接依存
- `services/ai/provider_ollama.py`
- `services/ai/provider_gemini.py`
- `services/ai/provider_huggingface.py`
- `services/ai/llm_common.py`

### 設定ファイル
- `config/llm_config.yaml`
- `.env`

---

## 🚀 今後の拡張予定

- [ ] Claude API統合
- [ ] GPT-4o API統合
- [ ] ストリーミング応答対応
- [ ] 会話履歴管理強化
- [ ] カスタムプロンプトテンプレート

---

*最終更新: 2025年11月2日*
