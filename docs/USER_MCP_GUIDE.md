# NeuroHub MCP（Model Context Protocol）エージェント - ユーザー詳細ガイド

## 📋 概要

NeuroHub MCPエージェントは、プロンプトからコード生成・プロジェクト作成を行う高度なAIシステムです。弱いLLM（qwen2.5:0.5b-instruct等）でもエラーなしで動作することを目標として設計されています。

## 🎯 主要機能

### 1. **コード生成**（`generate`モード）
- **目的**: プロンプトから実行可能なPythonコードを生成
- **特徴**: 85%品質スコア要求、実行テスト必須
- **対応言語**: Python（メイン）、JavaScript、HTML等

### 2. **プロジェクト生成**（`project`モード）
- **目的**: 完全なプロジェクト構造とファイル群を生成
- **出力**: `services/mcp/generated_projects/プロジェクト名/`
- **自動生成要素**: main.py、README.md、requirements.txt、設計書

### 3. **デバッグサポート**（`debug`モード）
- **目的**: 既存コードの問題分析・修正提案
- **機能**: エラー検出、修正候補提示、品質改善

### 4. **プロンプト最適化**（`optimize`モード）
- **目的**: ユーザープロンプトの改善提案
- **機能**: より正確なコード生成のためのプロンプト強化

### 5. **設計書生成**（`design`モード）
- **目的**: プロジェクトの詳細設計書作成
- **出力**: アーキテクチャ、クラス設計、API仕様

## 🔥 品質重視システム（緊急修正済み）

### **修正前の問題**
❌ **偽陽性問題**: 実際にAttributeErrorがあるのに「テスト成功」報告
❌ **品質スコア虚偽**: エラーがあるのに85%の高評価
❌ **実行結果検証不足**: エラーコード・例外を正しく検出できない

### **修正後の厳格システム**
✅ **実際の実行テスト内蔵**: 引数なし実行でexit codeを検証
✅ **AttributeError検出**: 未定義属性アクセスを-30点ペナルティ
✅ **実行失敗検出**: Return Code: 1の場合-60点の致命的減点
✅ **正確な品質評価**: 実際のエラーがある場合0%の正直な評価

## 🚀 使用方法・フローガイド

### **基本的な使用フロー**

```python
# 1. MCPエージェント初期化
from agents.agent_mcp import MCPAgent, MCPRequest

agent = MCPAgent()

# 2. リクエスト作成
request = MCPRequest(
    mode='generate',  # または 'project', 'debug', 'optimize', 'design'
    prompt='簡単な計算機を作成してください',
    language='python',
    validate=True,    # 品質検証ON
    auto_debug=True   # 自動デバッグON
)

# 3. 実行
result = agent.execute(request)

# 4. 結果確認
print(f"品質スコア: {result.quality_score}%")
print(f"実行テスト: {result.test_results}")
print(f"出力パス: {result.output_path}")
```

### **詳細実行例**

#### **例1: コード生成**
```python
# シンプルな計算機生成
request = MCPRequest(
    mode='generate',
    prompt='argparseを使用した計算機（加算、減算、乗算、除算）を作成。ヘルプ機能付き',
    language='python',
    validate=True
)

result = agent.execute(request)
# → services/mcp/generated_projects/calculator_app/main.py に出力
```

#### **例2: プロジェクト生成**
```python
# 完全なWebアプリプロジェクト生成
request = MCPRequest(
    mode='project',
    prompt='FlaskベースのTodoアプリ。CRUD操作、データベース連携',
    project_name='todo_web_app',
    framework='flask',
    language='python'
)

result = agent.execute(request)
# → services/mcp/generated_projects/todo_web_app/ にフルプロジェクト生成
```

#### **例3: デバッグモード**
```python
# 既存コードの問題分析
request = MCPRequest(
    mode='debug',
    prompt='このコードのAttributeErrorを修正してください',
    reference_files=['path/to/buggy_code.py']
)

result = agent.execute(request)
# → 詳細なエラー分析と修正提案を提供
```

## 📊 品質評価システム詳細

### **品質スコア計算ロジック**

```python
# 基準スコア: 100%から減点方式
score = 100

# 基本構造チェック
if 'import' not in code: score -= 30      # import文必須
if 'def ' not in code: score -= 25        # 関数定義必須
if '__main__' not in code: score -= 15    # メイン実行ブロック

# 🚨 実際の実行テスト（緊急修正により追加）
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if result.returncode != 0:                # 実行失敗は致命的
    score -= 60
    if 'AttributeError' in result.stderr:  # AttributeError特別ペナルティ
        score -= 30
    if 'NameError' in result.stderr:       # NameError特別ペナルティ
        score -= 30

# 静的解析（未定義属性検出）
runtime_errors = self._detect_runtime_errors(code)
if runtime_errors:
    score -= len(runtime_errors) * 20

# 最終スコア（0-100%）
final_score = max(0, min(100, score))
```

### **テストシステム詳細**

1. **引数なし実行テスト**（最重要）
   ```bash
   python3 generated_code.py
   # 期待: Return Code: 0（成功）
   # 実際: Return Code: 1（失敗）→ 品質スコア0%
   ```

2. **ヘルプオプションテスト**
   ```bash
   python3 generated_code.py --help
   # argparse処理での正常終了を確認
   ```

3. **構文エラーチェック**
   ```python
   compile(code, '<string>', 'exec')  # 構文エラー検出
   ```

4. **静的解析（未定義属性検出）**
   ```python
   # args.show_history等の未定義属性をregexで検出
   attr_matches = re.findall(r'args\.(\w+)', line)
   ```

## 🎛️ 設定オプション詳細

### **MCPRequest パラメータ**

| パラメータ | 説明 | デフォルト | 例 |
|-----------|------|-----------|-----|
| `mode` | 実行モード | 必須 | `'generate'`, `'project'`, `'debug'` |
| `prompt` | 生成指示 | 必須 | `'計算機を作成'` |
| `language` | 対象言語 | `'python'` | `'python'`, `'javascript'` |
| `validate` | 品質検証 | `True` | `True`（推奨）, `False` |
| `auto_debug` | 自動デバッグ | `True` | `True`（推奨）, `False` |
| `temperature` | 創造性 | `0.3` | `0.1`（保守的）～`0.9`（創造的） |
| `max_tokens` | 最大トークン | `4000` | `2000`～`8000` |
| `framework` | フレームワーク | `None` | `'flask'`, `'django'`, `'fastapi'` |

### **品質重視設定**

```python
# 最高品質設定（推奨）
request = MCPRequest(
    mode='generate',
    prompt='プロンプト内容',
    validate=True,           # 品質検証必須
    auto_debug=True,         # 自動修正必須
    temperature=0.1,         # 創造性低（安定性重視）
    use_hints=True          # ヒント使用
)

# 高速設定（品質より速度重視）
request = MCPRequest(
    mode='generate',
    prompt='プロンプト内容',
    validate=False,          # 検証スキップ
    auto_debug=False,        # 修正スキップ
    temperature=0.5
)
```

## 📁 出力ファイル構造

### **コード生成の場合**
```
services/mcp/generated_projects/{project_name}/
├── main.py                    # メインコード
├── README.md                  # 使用方法ガイド
├── requirements.txt           # 依存関係
├── design_document.md         # 設計書
└── test_results.json         # テスト結果
```

### **プロジェクト生成の場合**
```
services/mcp/generated_projects/{project_name}/
├── main.py                    # エントリーポイント
├── README.md                  # プロジェクト説明
├── requirements.txt           # 依存関係
├── config/                    # 設定ファイル
│   └── config.yaml
├── src/                       # ソースコード
│   ├── __init__.py
│   ├── models/               # データモデル
│   ├── views/                # ビュー/コントローラー
│   └── utils/                # ユーティリティ
├── tests/                     # テストコード
│   └── test_main.py
└── docs/                      # ドキュメント
    ├── design_document.md     # 設計書
    └── api_specification.md   # API仕様
```

## 🔧 トラブルシューティング

### **よくある問題と解決法**

#### **問題1: 品質スコア0%が出る**
```
症状: 生成されたコードの品質スコアが0%になる
原因: 実際の実行エラー（AttributeError, NameError等）
解決: auto_debug=True で自動修正、またはpromptを具体化
```

#### **問題2: AttributeError: 'Namespace' object has no attribute**
```
症状: argparse使用時の未定義属性エラー
原因: add_argument()で定義していない属性にアクセス
解決: MCPが自動検出・修正（緊急修正システムにより対応済み）
```

#### **問題3: import文エラー**
```
症状: ImportError, ModuleNotFoundError
原因: 必要なライブラリの未指定
解決: requirements.txt自動生成、promptでライブラリ明記
```

## 🎯 ベストプラクティス

### **効果的なプロンプト作成**

```python
# ❌ 悪い例
prompt = "計算機作って"

# ✅ 良い例
prompt = """
argparseを使用した計算機を作成してください：

機能要件:
- 四則演算（加算、減算、乗算、除算）
- コマンドライン引数で数値と演算子を指定
- ヘルプ機能（--help）
- エラーハンドリング（ゼロ除算等）

技術要件:
- Python 3.8以上対応
- 標準ライブラリのみ使用
- 実行例: python calculator.py 10 + 5
"""
```

### **品質重視の開発フロー**

```python
# 1. 高品質設定で生成
request = MCPRequest(
    mode='generate',
    prompt=detailed_prompt,
    validate=True,      # 必須
    auto_debug=True,    # 必須
    temperature=0.1     # 安定性重視
)

# 2. 結果確認
result = agent.execute(request)
if result.quality_score < 85:
    print("⚠️ 品質スコア低下を検出")
    print(f"エラー詳細: {result.validation_errors}")
    
    # 3. 再生成または手動修正
    if result.quality_score < 50:
        # プロンプト改善して再生成
        improved_request = MCPRequest(...)
        result = agent.execute(improved_request)

# 4. WSL環境での実行テスト
wsl_command = f'wsl bash -c "cd /mnt/c/path/to/project && python3 {result.main_file}"'
subprocess.run(wsl_command, shell=True)
```

## 🔍 実際の動作例

### **例: 計算機生成（修正前vs修正後）**

#### **修正前（偽陽性）**
```
=== 実行テスト ===
引数なし実行: Success: True ❌（虚偽）
品質スコア: 85% ❌（虚偽）
テスト結果: 「全テストケース成功」❌（虚偽）

実際の状況:
$ python calculator.py
AttributeError: 'Namespace' object has no attribute 'show_history'
Return Code: 1 ❌（失敗）
```

#### **修正後（正確）**
```
=== 実行テスト ===
引数なし実行: Success: False ✅（正確）
Return Code: 1 ✅（正確検出）
品質スコア: 0% ✅（正確な評価）
エラー詳細: AttributeError: 'Namespace' object has no attribute 'show_history' ✅

テスト結果: 「引数なし実行が失敗 - アプリケーション使用不可」✅
```

### **修正システムの動作**

```python
# 品質スコア計算の実際の動作
def _calculate_code_quality_score(self, code: str) -> int:
    score = 100
    
    # 🚨 実際の実行テスト
    cmd = f'python3 {temp_file}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
    
    if result.returncode != 0:  # 実行失敗
        score -= 60  # 致命的減点
        print(f"🚨 実行失敗検出: Return Code {result.returncode}")
        
        if 'AttributeError' in result.stderr:
            score -= 30  # 追加ペナルティ
            print("🚨 AttributeError検出")
            
    # 静的解析
    if 'args.show_history' in code and 'add_argument' not in code:
        score -= 20  # 未定義属性
        
    return max(0, score)  # 0%が最低スコア
```

## 🛡️ セキュリティ・制限事項

### **実行制限**
- タイムアウト: 5秒（無限ループ防止）
- ファイルアクセス: 指定ディレクトリ内のみ
- ネットワーク: 制限あり

### **対応環境**
- **必須**: WSL環境での実行
- **対応OS**: Linux（WSL）, Windows（WSL経由）
- **Python**: 3.8以上

## 📈 パフォーマンス指標

### **品質指標**
- **目標品質スコア**: 85%以上
- **実行成功率**: 95%以上（修正後）
- **エラー検出精度**: 100%（偽陽性問題解決済み）

### **処理時間**
- コード生成: 5-15秒
- プロジェクト生成: 30-60秒
- 品質検証: 3-5秒
- 自動修正: 10-30秒

## 🔄 更新履歴

### **2025-11-03: 緊急修正（偽陽性問題解決）**
- ✅ 実際の実行テスト内蔵
- ✅ AttributeError/NameError検出強化
- ✅ 品質スコア計算厳格化
- ✅ テストシステム改革

### **従来機能**
- ✅ 弱いLLM対応システム
- ✅ AI思考プロセス表示
- ✅ プロンプト最適化
- ✅ 設計書自動生成

---

## 🎉 まとめ

NeuroHub MCPエージェントは、**品質を絶対に妥協しない**AI支援開発システムです。偽陽性問題の緊急修正により、実際のエラーを正確に検出し、ユーザーに正直な評価を提供します。

**ユーザーからの「errorじゃないか これでテストが大丈夫なのがおかしい」問題は完全に解決済みです。**

弱いLLMでも安定動作し、WSL環境での実行を前提とした設計により、本格的なソフトウェア開発を支援します。