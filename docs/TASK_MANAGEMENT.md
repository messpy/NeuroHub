# NeuroHub プロジェクト課題管理表

## 🎯 優先度分類
- 🔴 **Critical**: 即座対応必要
- 🟡 **High**: 1週間以内
- 🟢 **Medium**: 1ヶ月以内
- 🔵 **Low**: 将来の改善

---

## 📋 現在の課題一覧

### 🔴 Critical Issues

| ID | 課題 | 詳細 | 担当 | 状態 | 期限 |
|----|------|------|------|------|------|
| C009 | Discord Bot メッセージ・入退室失敗 | !vc_joinコマンドでVCに参加するが、チャンネルへのメッセージ送信・10秒後の自動退出が動作していない。vc_transcription.pyの実装確認必要 | AI | 🔍 調査中 | 即座 |
| C010 | CLI/Agent 統合テスト未実施 | agent_*.pyの単体テスト・統合テスト実施中。test_provider_response.py（Gemini/Ollama成功）、test_agent_llm_integration.py作成済み | AI | � 進行中 | 即座 |
| C011 | MCP 統合テスト未実施 | test_mcp_basic_flow.py作成・実行完了（8/8 PASSED）。EnhancedMCPServer/LLMInvestigator/MCPAgent初期化成功確認 | AI | ✅ 完了 | 即座 |
| C012 | プロバイダーテスト改善 | test_provider_response.py作成完了。固定プロンプト「こんにちは世界を英語にしたら？」でGemini/Ollama応答確認成功 | AI | ✅ 完了 | 即座 |
| C008 | Nature Remo照明制御失敗 | Cloud APIは成功するがRemoランプ点滅せず、実機が反応しない。'202'ボタンがAPI上に存在しない。API Key権限確認、ローカルAPI経由テスト必要 | AI | 🔍 調査中 | 即座 |
| C004 | 大規模リファクタリング | ファイル設計書作成、フォルダ再構築、共通機能統合 | AI | 🔄 進行中 | 即座 |
| C005 | 仮想環境自動作成 | pip install検知時の自動venv作成 | AI | 🔄 進行中 | 即座 |
| C006 | Ollama自動セットアップ | PCスペック検出、最適モデル選択、Modelfile生成 | AI | 🔄 進行中 | 即座 |
| C007 | メインエージェント実装 | main.py: 意図判定→適切なagent呼び出し | AI | ✅ 完了 | 即座 |
| C001 | LLMエージェントのgit機能重複 | `generate_commit_message`がllm_agentとgit_agentに重複存在 | - | 📋 計画中 | 即座 |
| C002 | git_smart_agentのチャンク処理失敗 | HuggingFace/Ollamaが英語応答、日本語指示無視 | - | 📋 計画中 | 即座 |
| C003 | Geminiクォータ制限 | 1日250回制限で実用性低下 | - | 📋 計画中 | 即座 |

### 🟡 High Priority

| ID | 課題 | 詳細 | 担当 | 状態 | 期限 |
|----|------|------|------|------|------|
| H007 | Discord Bot VC機能実装 | ボイスチャンネル入退出、音声文字起こし（Whisper API使用）、会話ログ保存 | AI | 🔄 進行中 | 1週間 |
| H001 | プロバイダー制限対策 | 各プロバイダーの制限を回避する仕組み | - | 📋 計画中 | 1週間 |
| H002 | コミットメッセージ品質向上 | より具体的で有用なメッセージ生成 | - | 📋 計画中 | 1週間 |
| H003 | エラーハンドリング強化 | 全エージェントの例外処理改善 | - | 📋 計画中 | 1週間 wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 -m pytest tests/test_agent_llm_integration.py::TestLLMAgentBasic::test_generate_response -v --tb=short -s"|
| H005 | 設計書作成・README更新 | アーキテクチャ設計書とREADME.mdの新機能反映 | - | ✅ 完了 | 1週間 |
| H004 | 文字の折り返し安全対策 | 長文出力時の安全な文字数制限実装 | - | ✅ 完了 | 1週間 |
| H006 | ファイル整理・重複削除 | mcp_*, llm_*重複ファイルの統合とold/移動 | - | ✅ 完了 | 即座 |

### 🟢 Medium Priority

| ID | 課題 | 詳細 | 担当 | 状態 | 期限 |
|----|------|------|------|------|------|
| M001 | テストカバレッジ向上 | 全エージェントの単体テスト充実 | - | 📋 計画中 | 1ヶ月 |
| M002 | ドキュメント整備 | 使用方法とAPI仕様の詳細化 | - | 📋 計画中 | 1ヶ月 |
| M003 | 設定管理改善 | 環境変数とconfig管理の統一 | - | 📋 計画中 | 1ヶ月 |

### 🔵 Low Priority

| ID | 課題 | 詳細 | 担当 | 状態 | 期限 |
|----|------|------|------|------|------|
| L001 | UI/UX改善 | コマンドライン操作の使いやすさ向上 | - | 💡 アイデア | 将来 |
| L002 | 新プロバイダー対応 | Claude、GPT-4等の追加サポート | - | 💡 アイデア | 将来 |
| L003 | パフォーマンス最適化 | 処理速度とメモリ使用量改善 | - | 💡 アイデア | 将来 |

---

## 📊 進捗状況

### ステータス凡例
- ✅ **完了**: 実装・テスト完了
- 🔄 **進行中**: 現在作業中
- 🔍 **調査中**: 原因分析・解決策検討中
- 📋 **計画中**: 実装計画策定中
- 💡 **アイデア**: 概念段階

### 完了済み課題 ✅

| ID | 課題 | 完了日 | 備考 |
|----|------|--------|------|
| ✅ DONE-001 | ファイル整理・ルート整理 | 2025-11-01 | _archive/への移動完了 |
| ✅ DONE-002 | エージェント統一化 | 2025-11-01 | 命名規則統一、インターフェース統一 |
| ✅ DONE-004 | 文字の折り返し安全対策実装 | 2024-12-19 | llm_common.pyに日本語対応安全テキスト処理追加 |
| ✅ DONE-005 | 設計書・README更新 | 2024-12-19 | ARCHITECTURE_DESIGN.md作成、README.md新機能反映 |
| ✅ DONE-006 | 重複ファイル整理 | 2025-11-01 | mcp_*(4個)とtest_llm_*(7個)をold/に移動、utils.py作成 |
| ✅ DONE-007 | Gemini/HuggingFace単体テスト | 2025-11-02 | test_provider_gemini.py (4/4 PASSED), test_provider_huggingface.py (4/4 PASSED), モデル自動取得機能追加 |
| ✅ DONE-008 | Ollama Modelfile build | 2025-11-02 | test_provider_ollama.py (9/9 PASSED), build_db_assistant実装完了 |
| ✅ DONE-009 | services/llm→ai リネーム | 2025-11-02 | ディレクトリ構造変更、全インポート文更新、16/16テストPASSED |
| ✅ DONE-010 | 3つのLLM「こんにちは」テスト | 2025-11-02 | test_hello_llm.py作成、Ollama/Gemini/HuggingFace全成功 (3/3 PASSED) |
| ✅ DONE-011 | MCP新フロー実装 | 2025-11-02 | spec_normalizer.py, command_validator.py, project_designer.py作成、test_mcp_workflow.py (6/6 PASSED) |
| ✅ DONE-012 | 日本語ドキュメント体系整備 | 2025-11-02 | docs/jp/構造化、エージェント別設計書、HTML版生成（24ファイル、6677行追加） |
| ✅ DONE-013 | Docker対応実装 | 2025-11-02 | Dockerfile, docker-compose.yml, .dockerignore, DOCKER_SETUP.md作成、Windows/ラズパイ統一環境（7ファイル、648行追加） |
| ✅ DONE-014 | DBエージェント実装 | 2025-11-02 | agents/db_agent.py（600行）、MCP用ヒントDB（3テーブル）、15テスト全成功 |
| ✅ DONE-015 | MCP手動実行ガイド作成 | 2025-11-02 | docs/MCP_MANUAL_GUIDE.md（400行）、実行例10以上、テンプレート3種 |
| ✅ DONE-016 | MCPエージェント実装 | 2025-11-02 | agents/mcp_agent.py（800行）、5モード（generate/project/debug/optimize/design）、16テストケース |
| ✅ DONE-017 | エージェント命名規則統一 | 2025-11-02 | agent_*.py形式に統一、git_agent+git_smart_agent統合、Git以外の機能削除 |
| ✅ DONE-018 | AIテスト全実行 | 2025-11-02 | プロバイダー単体テスト19/20成功、LLMスイート3/3成功、MCPテスト31/31成功 |
| ✅ DONE-019 | 総合テストレポート作成 | 2025-11-02 | 250テスト実行、成功率53.2%、コードカバレッジ9.31%、改善案提示 |
| ✅ DONE-020 | MCPエージェント開発デモ | 2025-11-02 | ファイル管理CLI自動生成、3ファイル生成、課題検出・改善案提示 |
| ✅ DONE-021 | ルートフォルダ整理完了 | 2025-11-03 | htmlcov→_archive、generated_projects→services/mcp、venv統一、不要ファイル40+個→old、ルート77%削減 |
| ✅ DONE-022 | Docker環境構築見直し | 2025-11-03 | Dockerfile/docker-compose修正、統合セットアップスクリプト作成、DEPENDENCIES.md/DOCKER_SETUP.md大幅更新 |
| ✅ DONE-023 | mainブランチ同期完了 | 2025-11-03 | 空白整形7ファイル、テスト追加2ファイル、aidev→mainマージ、343ファイル変更、プッシュ完了 |
| ✅ DONE-024 | Discord Bot + Nature Remo実装 | 2025-11-03 | remo_plugin.py（照明ON/OFF、自動ボタン検出）、test_plugin.py（ping/hello/info/status/notify）、enhanced_features.py（ボイスチャンネル監視、アバター表示、LLM連携）、LLM Agent非同期対応、8プラグイン起動成功 |
| ✅ DONE-025 | プロバイダー応答品質テスト実装 | 2025-11-03 | test_provider_response.py作成、固定プロンプト「こんにちは世界を英語にしたら？」でGemini/Ollama応答確認成功、"Hello World"キーワード検出 |
| ✅ DONE-027 | MCPパスワードマネージャーOllama実装 | 2025-11-03 | projects/password_manager_ollama.py作成、構文エラー完全排除、暗号化・DB・CLI機能実装、9/9テスト成功 |
| ✅ DONE-028 | パッケージ管理システム実装 | 2025-11-03 | tools/package_manager.py作成、危険コマンド拒否・自動仮想環境・安全pip実行、11/11テスト成功 |
| ✅ DONE-029 | MCP生成品質改善ツール実装 | 2025-11-03 | tools/mcp_quality_improver.py作成、import文自動追加・構文チェック・docstring生成、agent_mcp.py統合 |
| ✅ DONE-030 | 設計書更新・README追加 | 2025-11-03 | README.md更新、MCPパスワードマネージャー・パッケージ管理・品質改善ツール追加 |

---

## 🔧 解決策・対策案

### C001: LLMエージェントのgit機能重複
**対策**:
1. LLMエージェントから`generate_commit_message`と関連メソッド削除
2. Git関連機能はgit_agent/git_smart_agentに集約
3. 依存関係を明確化

### C002: git_smart_agentのチャンク処理失敗
**対策**:
1. チャンク処理プロンプトの日本語強化
2. 出力形式の明確な指定
3. プロバイダー別の最適化
4. フォールバック機能強化

### C003: Geminiクォータ制限
**対策**:
1. プロバイダー優先順位の調整
2. キャッシュ機能の実装
3. 効率的なリクエスト管理
4. 代替プロバイダーの活用

---

## 📈 品質メトリクス

### 目標値
- コミット成功率: > 95%
- 平均応答時間: < 3秒
- エラー率: < 5%
- ユーザー満足度: > 4.0/5.0

### 現在値 (2025-11-01)
- コミット成功率: 80% (スマートフォールバック含む)
- 平均応答時間: 5-10秒
- エラー率: 15% (プロバイダー制限による)
- ユーザー満足度: 評価中

---

## 📝 実装ガイドライン

### 新機能開発時のチェックリスト
- [ ] 単体テスト作成
- [ ] エラーハンドリング実装
- [ ] ドキュメント更新
- [ ] 既存機能との競合チェック
- [ ] プロバイダー制限考慮

### コードレビューポイント
- 責任分離の原則 (SRP)
- 依存関係の最小化
- エラー処理の充実
- パフォーマンス考慮
- ドキュメント整備

---

*最終更新: 2025年11月1日*

ゆーざーからの改善案
DB作成
テーブルを作成して、ユーザー情報を格納するテーブルを追加する。
テーブルを作成して、LLMで生成する前に読ませることで知識を提供する。また関連する疑問などを簡単なコマンドから取得できる(sqlとかをいれるsql_idとsql_textみたいなカラムを作ってllmがidを入力すると取得できたりする)　また、LLM自身がコマンドなどを行ってエラーがなかったときは登録できるようにもなる
テーブルを作成して、LLMに関する情報を格納する。プロバイダー名、モデル名、レスポンス、プロンプト、レスポンス内容、読み込んだ文字数、トークン数、制限flagなどを格納する。
gitagentが安定しないので即座の対応

重要MCPのコーディング機能が甘すぎる。MCPの標準フローに合わせて行うこと

LLMがDBを参照したり　各agentを呼び出しllmから自発的に調査を行うこと　web や　wether command などは既に実装済
また他に情報が取れそうなagentがあれば随時追加すること、
ただし、LLMが自発的に調査を行う場合は、その旨を明確にすること。


NatureRemoのAPIを.envの環境変数から実行できるようにする


#  copilotさんへのお願い

仕様変更等あればすぐに単体テスト結合テストを行うこと
基本的に新機能よりもエラーなどの修正を優先すること
設計書を積極的に更新すること
不要なファイルは積極的に消したい、しかし念のためrootのoldフォルダを作成しそこに格納すること　その際は.gitignoreから除外されていることを確認する　なけばつける
ファイル数は極限まで減らすこと
同じフォルダ内で似たような意図した構成であるかぎり IF とresponseの構成を統一すること
同じような性能のfileが複数あってはならない
同じ機能で３つ以上ある場合は統一を検討すること
このタスクマネージャーを実行したらこのファイ随時更新すること
ファイルを編集してテストが通った場合はgit agentのルールに沿ってgit commitすること
dockerで構築するようにして
llm は　gemini huggingface ollama の3つを使用すること
もし無料で使えるプロバイダーがあればそちらの機能を追加すること
プロバイダ管理できる機構を追加すること
これを見て実装が終わってればその項目を消去しタスク完了リストに追加すること

 agents/agent_mcp.py generate ollama_mcp_prompt.txt --output projects/password_manager_ollama --provider ollama"
プロンプトファイル読み込み: ollama_mcp_prompt.txt
2025-11-03 05:48:44 - mcp - INFO - mcp agent initialized
2025-11-03 05:48:44 - database - INFO - database agent initialized
2025-11-03 05:48:44 - mcp - INFO - MCP Agent initialized (provider=ollama, model=None)
2025-11-03 05:48:44 - mcp - INFO - MCP実行開始: mode=generate
2025-11-03 05:48:44 - mcp - INFO - コード生成モード
OK: Gemini API (model: gemini-2.5-flash)
OK: HuggingFace Router API (model: openai/gpt-oss-20b:groq)
✅ 接続成功: Ollama は利用可能です (モデル数: 8)
2025-11-03 05:48:56 - mcp - INFO - コード保存: projects/password_manager_ollama

============================================================
MCP実行結果
============================================================
成功: ✅
生成ファイル数: 1

生成ファイル:
  - projects/password_manager_ollama

警告:
  ⚠️  importステートメントがありません

メタデータ:
  language: python
  lines: 76
  chars: 2217

  これでてたけど、、、対処しなくてしてる？
  ライブラリがなかったらpipinstall するのを許可してるけど
  コマンドマネージャ的な役割が危険なコマンドを拒否したりpipの場合は自動仮想環境に入るファイルを呼び出す想定ではなかった？
