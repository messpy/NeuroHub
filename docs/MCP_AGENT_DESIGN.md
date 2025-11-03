# MCP (Model Context Protocol) Agent 設計書

## 概要

MCPエージェントは、プロンプトからコード生成・プロジェクト作成を自動化するエージェントです。弱いLLMでもエラーなしで動作することを目指し、包括的な品質チェックと自動修正機能を提供します。

## アーキテクチャ

### 全体構成

```
MCPAgent
├── コア実行機能
│   ├── execute() - メイン実行ルーチン
│   ├── _generate_code() - コード生成
│   ├── _generate_project() - プロジェクト生成
│   ├── _debug_code() - デバッグサポート
│   ├── _optimize_prompt() - プロンプト最適化
│   └── _generate_from_design() - 設計書参照生成
├── プロンプト処理機能
│   ├── _build_system_message() - システムメッセージ構築
│   ├── _build_full_prompt() - プロンプト構築
│   └── _get_relevant_hints() - ヒント取得
├── プロジェクト生成機能
│   ├── _create_project_directory() - ディレクトリ作成
│   ├── _generate_project_name() - プロジェクト名生成
│   ├── _validate_and_fix_project_name() - 名前検証
│   ├── _create_design_document() - 設計書作成
│   └── _generate_readme() - README生成
├── コード品質・デバッグ機能
│   ├── _comprehensive_auto_fix_loop() - 自動修正ループ
│   ├── _detect_runtime_errors() - エラー検出
│   ├── _fix_execution_errors() - エラー修正
│   ├── _calculate_code_quality_score() - 品質スコア計算
│   ├── _strict_syntax_check() - 構文チェック
│   └── _strict_execution_test() - 実行テスト
└── ヘルパー・ユーティリティ機能
    ├── _extract_code() - コード抽出
    ├── _save_generated_code() - コード保存
    ├── _save_readme() - README保存
    └── _execute_final_tests_and_review() - 最終テスト・レビュー
```

### データフロー

```
ユーザー入力 (CLI)
    ↓
MCPRequest作成
    ↓
execute() - モード判定
    ↓
各処理モード実行
    ↓
LLMエージェント呼び出し
    ↓
コード生成・抽出
    ↓
品質チェック・自動修正
    ↓
ファイル保存
    ↓
MCPResult返却
```

## 主要機能

### 1. コード生成 (generate)

**機能**: プロンプトから実行可能なコードを生成

**フロー**:
1. プロジェクト名生成
2. システムメッセージ・プロンプト構築
3. LLM実行
4. コード抽出
5. 自動エラー修正ループ
6. 実装後レビュー
7. ファイル保存
8. README生成
9. 最終テスト・レビュー

**出力**: 実行可能なPythonファイル + README

### 2. プロジェクト生成 (project)

**機能**: 完全なプロジェクト構造を生成

**フロー**:
1. プロジェクトディレクトリ作成
2. 設計書作成
3. メインコード生成
4. テストコード生成（オプション）
5. README生成（オプション）
6. requirements.txt生成
7. プロジェクトテスト
8. 期待値検証

**出力**: 完全なプロジェクト構造

### 3. デバッグサポート (debug)

**機能**: 既存コードのデバッグ・修正

### 4. プロンプト最適化 (optimize)

**機能**: LLM用プロンプトの最適化

### 5. 設計書参照生成 (design)

**機能**: 設計書に基づくコード生成

## 品質管理システム

### 自動修正ループ

```
入力コード
    ↓
構文チェック → 構文エラー修正
    ↓
実行テスト → 実行エラー修正
    ↓
ランタイムエラー検出 → 未定義属性修正
    ↓
品質スコア計算 (目標85%以上)
    ↓
基本完全性チェック
    ↓
修正完了 or 上限到達
```

### エラー検出・修正機能

1. **構文エラー**: Python構文の検証・修正
2. **実行エラー**: 実際の実行テストによるエラー検出
3. **未定義属性エラー**: argparse属性の未定義検出・修正
4. **品質スコア**: 総合的なコード品質評価

### 品質スコア計算要素

- import文の存在 (30点)
- 関数定義の存在 (25点)
- メイン実行ブロックの存在 (15点)
- コード長の適切さ (30点)
- 構文エラーなし (40点×エラー数)
- ランタイムエラーなし (50点×エラー数)

## 設定・カスタマイズ

### MCPRequest パラメータ

```python
@dataclass
class MCPRequest:
    mode: str                          # 実行モード
    prompt: str                        # プロンプト
    output_path: Optional[str]         # 出力パス
    language: str = 'python'           # プログラミング言語
    framework: Optional[str]           # フレームワーク
    temperature: float = 0.3           # LLM温度
    max_tokens: int = 4000            # 最大トークン数
    use_hints: bool = True            # ヒント使用
    validate: bool = True             # バリデーション
    auto_debug: bool = True           # 自動デバッグ
    project_name: Optional[str]       # プロジェクト名
    project_type: Optional[str]       # プロジェクトタイプ
    include_tests: bool = True        # テスト生成
    include_docs: bool = True         # ドキュメント生成
```

### LLMプロバイダー対応

- **Ollama**: ローカル実行、高速
- **Gemini**: 高品質、制限あり
- **HuggingFace**: 無料、Router API

## CLI インターフェース

### 基本的な使用方法

```bash
# 基本のコード生成
python3 agent_mcp.py generate "パスワード生成ツールを作って"

# プロバイダー指定
python3 agent_mcp.py generate "計算機アプリ" --provider gemini

# 短縮形（modeなしで自動判定）
python3 agent_mcp.py "ランダム数字ツール" --provider ollama

# プロジェクト生成
python3 agent_mcp.py project "Webアプリケーション" --project-name my_app

# 詳細オプション
python3 agent_mcp.py generate "API作成" \
  --language python \
  --framework flask \
  --temperature 0.1 \
  --max-tokens 2000 \
  --output /path/to/output.py
```

### オプション一覧

| オプション | 短縮形 | デフォルト | 説明 |
|-----------|--------|-----------|------|
| --output | -o | - | 出力ファイルパス |
| --project-name | - | - | プロジェクト名 |
| --project-type | - | - | プロジェクトタイプ (cli/web/api/lib) |
| --language | -l | python | プログラミング言語 |
| --framework | -f | - | フレームワーク名 |
| --provider | - | ollama | LLMプロバイダー |
| --model | -m | - | LLMモデル名 |
| --temperature | -t | 0.3 | Temperature |
| --max-tokens | - | 4000 | 最大トークン数 |

## エラーハンドリング

### 一般的な問題と解決策

1. **LLM接続エラー**
   - **症状**: `全プロバイダーで失敗` エラー
   - **解決**: プロバイダー設定確認、ネットワーク確認

2. **構文エラー**
   - **症状**: `SyntaxError` 発生
   - **解決**: 自動修正機能が適用、手動確認が必要な場合あり

3. **未定義属性エラー**
   - **症状**: `AttributeError: 'Namespace' object has no attribute 'xxx'`
   - **解決**: 自動的にargparse定義を追加

4. **品質スコア低下**
   - **症状**: 品質スコア85%未満
   - **解決**: 自動修正ループが実行、必要に応じて手動調整

## パフォーマンス

### 最適化されている要素

- **Web検索の無効化**: パフォーマンス向上のため一時的に無効
- **修正ループの制限**: 最大5回の試行で無限ループ防止
- **キャッシュ機能**: プロジェクト名生成の高速化

### ボトルネック

- **LLM生成時間**: プロバイダーとモデルに依存
- **品質チェック**: 複数回の構文・実行テスト
- **ファイルI/O**: 大量のファイル生成時

## セキュリティ

### 考慮事項

1. **コード実行リスク**: 生成されたコードの自動実行
2. **ファイルシステムアクセス**: 指定ディレクトリへの書き込み
3. **LLMプロンプトインジェクション**: 悪意のあるプロンプト入力

### 対策

1. **サンドボックス実行**: 一時ファイルでの実行テスト
2. **パス制限**: 指定されたディレクトリ内でのみファイル作成
3. **入力検証**: プロンプトの基本的な検証

## トラブルシューティング

### よくある問題

1. **`args.xxx` 属性エラー**
   ```
   AttributeError: 'Namespace' object has no attribute 'database'
   ```
   **原因**: argparseで定義されていない属性へのアクセス
   **解決**: 自動修正機能で`add_argument`を追加

2. **構文エラーが修正されない**
   ```
   SyntaxError: 'return' outside function
   ```
   **原因**: 関数外でのreturn文使用
   **解決**: 手動でのコード構造確認が必要

3. **品質スコア0%**
   **原因**: 複数のエラーが重複
   **解決**: 自動修正を無効にして単純な生成を試す

### デバッグ手順

1. **ログ確認**: MCPエージェントのログで詳細確認
2. **段階的テスト**: 各機能を個別にテスト
3. **手動修正**: 自動修正が効かない場合の手動対応
4. **設定変更**: プロバイダーやパラメータの調整

## 拡張性

### 新機能追加

1. **新しい実行モード**: `execute()`メソッドに追加
2. **新しい言語サポート**: 言語別の処理を追加
3. **新しいLLMプロバイダー**: プロバイダー設定を拡張

### カスタマイズポイント

1. **システムメッセージ**: `_build_system_message()`をカスタマイズ
2. **品質基準**: `_calculate_code_quality_score()`を調整
3. **修正ロジック**: `_fix_execution_errors()`を拡張

## 今後の改善予定

### 短期的な改善

1. **修正機能の強化**: より多くのエラーパターンに対応
2. **テストカバレッジ向上**: 単体テストの追加
3. **ドキュメント整備**: 詳細な使用例とトラブルシューティング

### 長期的な改善

1. **WebUI提供**: ブラウザベースのインターフェース
2. **プラグインシステム**: サードパーティ拡張の対応
3. **クラウド連携**: 外部サービスとの統合

## 技術仕様

### 依存関係

```
agents/
├── common.py           # BaseAgent
├── agent_llm.py       # LLMAgent
├── agent_db.py        # DatabaseAgent
└── agent_mcp.py       # MCPAgent
```

### 設定ファイル

```
config/
├── config.yaml        # 基本設定
├── llm_config.yaml    # LLM設定
└── agent_config.yaml  # エージェント設定
```

### 出力構造

```
services/mcp/generated_projects/
├── project_name/
│   ├── main.py
│   ├── README.md
│   ├── requirements.txt
│   └── test_project_name.py
```

このMCPエージェントは、自動化されたコード生成と品質管理を通じて、効率的な開発支援を提供します。
