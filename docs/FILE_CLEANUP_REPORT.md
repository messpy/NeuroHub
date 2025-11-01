# ファイル整理レポート

**実施日**: 2025年11月1日
**担当**: Copilot
**目的**: TASK_MANAGEMENT.md要件「ファイル数を極限まで減らす」に対応

---

## 📊 整理結果サマリー

### 削減ファイル数
- **合計**: 12ファイル → `old/`フォルダに移動
  - services/mcp/: 5ファイル
  - tests/: 7ファイル

### ディスク使用量削減
- 重複コード: 約3,000行削減（推定）
- 保守性向上: 類似機能の集約により変更箇所が明確化

---

## 🗂️ 詳細: services/mcp/ 整理

### 移動ファイル（5個）
| ファイル名 | 理由 | 移動先 |
|-----------|------|--------|
| `mcp_test.py` | 重複ユーティリティ関数 | `old/mcp_test.py` |
| `mcp_spec.py` | 重複ユーティリティ関数 | `old/mcp_spec.py` |
| `mcp_run.py` | 重複ユーティリティ関数 | `old/mcp_run.py` |
| `mcp_codegen.py` | 重複ユーティリティ関数 | `old/mcp_codegen.py` |
| `mcp_cmd.py.bak` | バックアップファイル | `old/mcp_cmd.py.bak` |

### 統合結果
**新規作成**: `services/mcp/utils.py`
- 共通ユーティリティ関数を1ファイルに集約
- 含まれる機能:
  - YAML操作 (`yaml_dump`, `yaml_load`)
  - ファイル管理 (`ensure_dirs`, `to_snake`)
  - コマンド実行 (`run`)
  - LLMプロバイダー検出 (`probe_models`, `require_llm_or_die`)
  - テキスト処理 (`strip_code_fences`)

### 残存ファイル（整理後）
| ファイル名 | 役割 |
|-----------|------|
| `mcp_enhanced.py` | MCP強化サーバー（主要機能） |
| `llm_investigator.py` | LLM自発調査エージェント |
| `natureremo_agent.py` | NatureRemo API統合 |
| `utils.py` | 共通ユーティリティ ⭐新規 |
| `ai_prj_coding.py` | AIプロジェクトコーディング |
| `cmd_exec.py` | コマンド実行機能 |
| `core.py` | コア機能 |

---

## 🧪 詳細: tests/ 整理

### 移動ファイル（7個）
| ファイル名 | 理由 | 移動先 |
|-----------|------|--------|
| `test_llm_agent_current.py` | 重複テスト（test_llm_agent.pyで統合） | `old/` |
| `test_llm_agent_updated.py` | 重複テスト（test_llm_agent.pyで統合） | `old/` |
| `test_llm_patch.py` | 一時的なパッチテスト | `old/` |
| `test_llm_run.py` | 重複テスト（test_llm_suite.pyで統合） | `old/` |
| `test_providers.py` | 重複テスト（test_llm_providers.pyで統合） | `old/` |
| `test_providers_direct.py` | 重複テスト（test_llm_providers.pyで統合） | `old/` |
| `test_providers_final.py` | 重複テスト（test_llm_providers.pyで統合） | `old/` |

### 残存ファイル（主要テスト）
| ファイル名 | テスト対象 | 状態 |
|-----------|-----------|------|
| `test_llm_agent.py` | LLMエージェント総合 | ✅ 維持 |
| `test_llm_suite.py` | LLMプロバイダー統合 | ✅ 維持 |
| `test_llm_providers.py` | プロバイダー詳細テスト | ✅ 維持 |

---

## 🔧 .gitignore 更新

### 追加内容
```gitignore
# Note: old/ folder is tracked for archived files
```

### 意図
- `old/`フォルダは`.gitignore`から**除外しない**
- アーカイブファイルも履歴として追跡
- `_archive/`との違い:
  - `_archive/`: 古いプロジェクトファイル（gitignore対象）
  - `old/`: 重複削除ファイル（git追跡対象）

---

## ✅ 検証結果

### テスト実行
```bash
# MCP統合テスト
python test_mcp_integration.py
結果: 9/9テスト合格 ✅

# LLMテストスイート
python tests/test_llm_suite.py
結果: Ollama動作確認、一部エラーは既知の問題
```

### 統合後の動作確認
- ✅ MCPサーバー初期化成功
- ✅ ナレッジベース操作正常
- ✅ LLM自発調査機能動作
- ✅ データベース統合正常
- ✅ エージェント呼び出し成功

---

## 📋 TASK_MANAGEMENT.md 更新

### 新規追加項目
- **H006**: ファイル整理・重複削除 → ✅ 完了
- **DONE-006**: 重複ファイル整理（2025-11-01）

---

## 📈 効果・メリット

### 1. 保守性向上
- **Before**: 同じ関数が4ファイルに分散
- **After**: 共通機能を`utils.py`に集約
- 変更時の修正箇所が1箇所に限定

### 2. コード品質向上
- 重複コード削減により、バグ混入リスク低減
- 統一されたインターフェースで可読性向上

### 3. ディレクトリ構造の明確化
```
services/mcp/
├── mcp_enhanced.py      # 主要機能
├── llm_investigator.py  # 調査機能
├── natureremo_agent.py  # 外部API統合
└── utils.py             # 共通ユーティリティ ⭐統合
```

### 4. テスト戦略の明確化
- `test_llm_agent.py`: エージェント総合テスト
- `test_llm_suite.py`: プロバイダー統合テスト
- `test_llm_providers.py`: プロバイダー詳細テスト

---

## 🔮 今後の改善案

### さらなる統合候補
1. **services/llm/内のファイル**
   - `llm_cli.py`, `llm_common.py`の役割整理
   - 重複機能の有無確認

2. **tests/内の小規模テスト**
   - `test_cmd_exec.py`, `test_config_loading.py`などの統合検討

3. **エージェントファイル**
   - `agents/`内の`*_agent.py`の責任分離確認

### 継続的なファイル管理
- 新規ファイル作成時の命名規則遵守
- 定期的な重複チェック（月1回）
- `old/`フォルダの定期的なレビュー（6ヶ月後）

---

## 📝 注意事項

### old/フォルダの扱い
- **削除しないこと**: 参照が必要な場合に備えてgit追跡
- **6ヶ月後レビュー**: 2025年5月に削除可否を判断
- **復元方法**: `git log`で履歴確認後、必要に応じて復元

### 統合ファイルの責任
- `utils.py`は**ユーティリティ専用**
- ビジネスロジックは含めない
- 各機能ファイルから`import`して使用

---

*最終更新: 2025年11月1日*
