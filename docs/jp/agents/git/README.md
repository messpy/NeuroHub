# Gitエージェント 概要

## 🎯 役割と責任

Gitエージェントは、Git操作を自動化し、LLMを活用したスマートなコミットメッセージ生成を行うエージェントです。

---

## 📋 主要機能

### 1. 基本Git操作（git_agent.py）
- `git status`実行
- `git diff`取得
- `git add`実行
- `git commit`実行
- `git push`実行

### 2. スマートコミット（git_smart_agent.py）
- 変更差分の自動チャンク処理
- LLM生成のコミットメッセージ
- プロバイダー自動切り替え
- 日本語コミットメッセージ生成

---

## 🏗️ アーキテクチャ

```
┌──────────────────────────────┐
│  Git Smart Agent             │
│                              │
│  - チャンク処理              │
│  - LLMコミットメッセージ生成  │
│  - フォールバック制御        │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐  ┌────▼────┐
│Git Agent│  │LLM Agent│
│         │  │         │
│- status │  │- Gemini │
│- diff   │  │- HF     │
│- commit │  │- Ollama │
└─────────┘  └─────────┘
```

---

## 🔧 使用方法

### 基本的なGit操作

```python
from agents.git_agent import GitAgent

agent = GitAgent()

# ステータス確認
status = agent.get_status()
print(status)

# 変更差分取得
diff = agent.get_diff()
print(diff)

# コミット
agent.commit("feat: 新機能追加")
```

### スマートコミット

```python
from agents.git_smart_agent import GitSmartAgent

agent = GitSmartAgent()

# 自動コミット（LLMがメッセージ生成）
result = agent.smart_commit()
# 出力例:
# feat(mcp): MCP新フロー実装
#
# ✅ 実装内容:
# - spec_normalizer.py追加
# - command_validator.py追加
```

---

## 📊 コミットメッセージ形式

### Conventional Commits準拠

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `test`: テスト
- `refactor`: リファクタリング
- `chore`: その他

#### 例
```
feat(llm): Geminiプロバイダー追加

✅ 実装内容:
- provider_gemini.py作成
- 自動モデル選択機能追加

📊 テスト結果:
- test_provider_gemini.py: 4/4 PASSED
```

---

## 🧪 テスト

### テストファイル
- `tests/test_git_agent.py`
- `tests/test_git_smart_agent.py`

### 実行コマンド
```bash
pytest tests/test_git_*.py -v
```

---

## 📖 関連ドキュメント

- [詳細設計](./DETAILED_DESIGN.md)
- [コミット戦略](./COMMIT_STRATEGY.md)
- [その他設計](./OTHER_DESIGNS.md)

---

*最終更新: 2025年11月2日*
