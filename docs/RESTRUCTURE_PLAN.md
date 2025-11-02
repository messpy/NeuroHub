# プロジェクト構造整理計画

**作成日**: 2025年11月2日
**目的**: プロジェクト構造を機能別に明確化し、保守性を向上

---

## 🎯 整理方針

### 1. **LLM関連の統合**
❌ 旧構造:
```
services/llm/  # 複数プロバイダー混在
├── provider_ollama.py
├── provider_gemini.py
├── provider_huggingface.py
└── modelfile_generator.py
```

✅ 新構造:
```
services/ollama/  # Ollama専用
├── provider_ollama.py
├── modelfile_generator.py
├── config/
│   └── ollama_config.yaml
└── modelfiles/
    ├── mcp_code_assistant.Modelfile
    └── db_assistant_light.Modelfile

services/gemini/  # Gemini専用（将来）
└── provider_gemini.py

services/huggingface/  # HuggingFace専用（将来）
└── provider_huggingface.py
```

**理由**: プロバイダー毎に独立させることで、依存関係を明確化

---

### 2. **設定ファイルの分離**
❌ 旧構造:
```
config/
├── discord_config.yaml  # Discord設定
├── llm_config.yaml      # LLM設定
├── config.yaml          # 全体設定
└── agent_config.yaml    # Agent設定
```

✅ 新構造:
```
config/
├── config.yaml         # プロジェクト全体設定のみ
└── agent_config.yaml   # Agent全般設定

services/discord/config/
└── discord_config.yaml  # Discord専用設定

services/ollama/config/
└── ollama_config.yaml   # Ollama専用設定

services/web/config/
└── web_config.yaml      # Web検索専用設定
```

**理由**: サービス毎に設定を分離し、依存を減らす

---

### 3. **tools/ の統合**
❌ 旧構造:
```
tools/
├── ollama_setup.py      # Ollama関連
├── websearch_cli.py     # Web検索関連
├── run_discord_bot.py   # Discord関連
└── git_helper.py        # Git関連
```

✅ 新構造:
```
services/ollama/
└── setup.py  # 旧ollama_setup.py

services/web/
└── cli.py    # 旧websearch_cli.py

services/discord/
└── cli.py    # 旧run_discord_bot.py

agents/
└── git_helper.py  # Git Agentのヘルパー
```

**理由**: 機能毎にツールを配置し、サービスと一体化

---

### 4. **不要ファイルの削除**
🗑️ 削除対象:
- `htmlcov_llm/` - 通常の`htmlcov/`に統一
- `modelfiles/` - `services/ollama/modelfiles/`に移動済み
- `services/llm/` - `services/ollama/`に統合後削除

✅ 実行済み:
- ✅ `htmlcov_llm/` 削除完了
- ✅ `modelfiles/` → `services/ollama/modelfiles/` 移動完了

---

## 📋 実行ステップ

### Phase 1: ディレクトリ構造作成 ✅ 完了
- [x] `services/ollama/config/` 作成
- [x] `services/ollama/modelfiles/` 作成
- [x] `services/discord/config/` 作成
- [x] `services/web/config/` 作成

### Phase 2: ファイル移動 🔄 進行中
- [x] `modelfiles/*` → `services/ollama/modelfiles/`
- [x] `htmlcov_llm/` 削除
- [ ] `services/llm/provider_ollama.py` → `services/ollama/`
- [ ] `services/llm/modelfile_generator.py` → `services/ollama/`
- [ ] `config/llm_config.yaml` → `services/ollama/config/ollama_config.yaml`
- [ ] `config/discord_config.yaml` → `services/discord/config/`

### Phase 3: インポートパス修正 ⏳ 未実施
主な修正対象:
- `agents/llm_agent.py`
- `main.py`
- `tests/test_llm_*.py`

修正例:
```python
# 旧
from services.llm.provider_ollama import OllamaConfig

# 新
```python
from services.llm.llm_common import load_config, LLMResponse
from services.llm.provider_ollama import OllamaConfig
```

### Phase 4: 設定ファイル更新 ⏳ 未実施
- [ ] `services/ollama/config/ollama_config.yaml` 作成
- [ ] `services/discord/config/discord_config.yaml` 移動
- [ ] `services/web/config/web_config.yaml` 作成

### Phase 5: tools/ 統合 ⏳ 未実施
- [ ] `tools/ollama_setup.py` → `services/ollama/setup.py`
- [ ] `tools/websearch_cli.py` → `services/web/cli.py`
- [ ] `tools/run_discord_bot.py` → `services/discord/cli.py`

### Phase 6: テスト実行 ⏳ 未実施
- [ ] WSLで全テスト実行
- [ ] インポートエラー修正
- [ ] 機能テスト（Ollama, Discord, Web）

---

## 🎯 期待される効果

### 保守性向上
- ✅ サービス毎に独立したディレクトリ
- ✅ 設定ファイルの明確な分離
- ✅ 依存関係の可視化

### 開発効率向上
- ✅ 必要なファイルがすぐに見つかる
- ✅ サービス追加が容易
- ✅ テストの実行範囲が明確

### Docker対応準備
将来的にDockerコンテナ化する際も、サービス毎に分離されているため容易:
```dockerfile
# services/ollama/ のみをコンテナ化
FROM python:3.11
COPY services/ollama/ /app/ollama/
...
```

---

## 📊 進捗状況

| フェーズ | 状態 | 完了率 |
|---------|------|--------|
| Phase 1: ディレクトリ作成 | ✅ 完了 | 100% |
| Phase 2: ファイル移動 | 🔄 進行中 | 40% |
| Phase 3: インポート修正 | ⏳ 未実施 | 0% |
| Phase 4: 設定更新 | ⏳ 未実施 | 0% |
| Phase 5: tools統合 | ⏳ 未実施 | 0% |
| Phase 6: テスト | ⏳ 未実施 | 0% |
| **全体** | 🔄 **進行中** | **23%** |

---

## 🚀 次のアクション

1. **即座に**: services/llmファイルをservices/ollamaに移動
2. 全インポートパスを一括検索・置換
3. WSLでテスト実行
4. エラー修正
5. 完了報告

---

**担当**: GitHub Copilot
**最終更新**: 2025-11-02 18:10 JST
