# 検索用データベースガイド

## 📊 データベース構造

### 1. **simple_search_results** (Web検索結果)
検索クエリと結果を保存します。

**カラム:**
- `term` (TEXT): 検索クエリ
- `title` (TEXT): 検索結果のタイトル
- `url` (TEXT): URL
- `snippet` (TEXT): 説明文
- `source` (TEXT): 検索ソース (wikipedia_ja, duckduckgo, google_search等)
- `confidence` (REAL): 信頼度 (0.0-1.0)
- `created_at` (DATETIME): 作成日時

**現在の内容例:**
```
- [wikipedia_ja] Python: Python...
- [wikipedia_en] BeautifulSoup: Beautiful Soup (HTML parser)...
- [wikipedia_ja] 機械学習: 機械学習...
```

**使用箇所:**
- `practical_web_searcher.py`: Web検索結果のキャッシュ
- 同じクエリを再検索しないための最適化

---

### 2. **web_page_content** (Webページ内容)
取得したWebページの完全な内容を保存します。

**カラム:**
- `url` (TEXT UNIQUE): ページURL
- `title` (TEXT): ページタイトル
- `main_content` (TEXT): メインコンテンツ
- `status_code` (INTEGER): HTTPステータスコード
- `load_time` (REAL): 読み込み時間
- `last_updated` (DATETIME): 最終更新日時

**現在の内容:** 0件（まだ使用されていない）

**使用箇所:**
- BeautifulSoupでスクレイピングしたページ内容の保存
- 詳細な情報が必要な場合のキャッシュ

---

### 3. **debug_history** (デバッグ履歴)
自動デバッグの試行履歴を保存します。

**カラム:**
- `project_name` (TEXT): プロジェクト名
- `error_type` (TEXT): エラータイプ (ImportError, NameError等)
- `error_message` (TEXT): エラーメッセージ
- `fix_prompt` (TEXT): 修正プロンプト
- `fix_code` (TEXT): 修正コード
- `success` (BOOLEAN): 成功/失敗
- `iterations` (INTEGER): 試行回数
- `provider` (TEXT): 使用LLMプロバイダー
- `created_at` (DATETIME): 作成日時

**現在の内容例:**
```
1. パスワード生成ツール_cli: None - 失敗 (20回)
2. 買い物リスト: None - 失敗 (20回)
3. じゃんけんゲーム: None - 失敗 (5回)
```

**使用箇所:**
- `auto_debugger.py`: 過去の成功パターン検索
- 同じエラーの解決方法を学習

---

### 4. **successful_patterns** (成功パターン)
成功したコード生成パターンを保存します。

**カラム:**
- `task_description` (TEXT): タスク説明
- `prompt_template` (TEXT): プロンプトテンプレート
- `generated_code` (TEXT): 生成されたコード
- `success_rate` (REAL): 成功率
- `usage_count` (INTEGER): 使用回数
- `provider` (TEXT): プロバイダー
- `created_at` (DATETIME): 作成日時

**使用箇所:**
- 成功したプロジェクト生成のパターンを再利用
- プロンプト最適化の参考

---

## 🔍 Web検索の仕組み

### エラー解決策検索のフロー

1. **エラータイプ抽出**
   ```
   ImportError, NameError, ArgumentError, etc.
   ```

2. **エラーキー抽出**
   ```
   "name 'random' is not defined" → "random is not defined"
   "conflicting option string: --help" → "conflicting option string"
   ```

3. **ローカル知識ベース検索（優先）**
   ```python
   solutions = {
       'ImportError': [
           "💡 不足モジュール: 必要なimport文を追加",
           "💡 標準ライブラリ: randomモジュールはimport randomが必要",
       ],
       'NameError': [...],
       'ArgumentError': [...],
   }
   ```

4. **Python公式ドキュメント検索**
   ```
   クエリ: "ImportError"
   検索先: https://docs.python.org/ja/3/search.html
   ```

5. **DuckDuckGo Web検索**
   ```
   クエリ: "Python ImportError solution"
   検索先: https://html.duckduckgo.com/html/
   結果: Stack Overflow、GitHubなど
   ```

6. **検索結果の統合**
   - ローカル知識: 3件
   - Python Docs: 1-2件
   - Web検索: 2-4件
   - **合計: 最大8件のヒント**

---

## 📝 ログ出力の改善

### 新しいログ出力内容

#### 1. エラー分析
```
🔍 エラータイプ抽出: ImportError
🔍 エラーキー抽出: cannot import name 'hide_password' from 'getpass'
```

#### 2. ローカル知識ベース
```
📚 ローカル知識ベース: 3件のヒント
   1. 💡 不足モジュール: 必要なimport文を追加してください
   2. 💡 モジュール名確認: getpass, hide_passwordなどの存在しない関数をimportしていないか確認
   3. 💡 標準ライブラリ: randomモジュールはimport randomが必要です
```

#### 3. Web検索
```
🔍 Python公式Docs検索: 'ImportError'
✅ 公式Docs発見: ImportError — Python 3.x ドキュメント

🔍 Web検索開始: 'Python ImportError solution'
✅ Web検索: 2件発見
   1. [duckduckgo] How to Fix Python ImportError - Stack Overflow
      > ImportError occurs when Python cannot find the module...
   2. [duckduckgo] Common Python Import Errors and Solutions
      > Check your module name and ensure it's installed...
```

#### 4. テストコマンド
```
🔍 構文チェック実行中...
   コマンド: python -m py_compile main.py
✅ 構文チェック成功

🔍 実行テスト中...
   コマンド: python main.py --help
   作業ディレクトリ: C:\Users\kenny\sandbox\NeuroHub\generated_projects\test_cli
❌ 実行テスト失敗 (終了コード: 1)
   エラー: Traceback (most recent call last):...
```

#### 5. LLMの思考プロセス
```
============================================================
🤖 LLM修正プロンプト送信 (ollama)
============================================================
📝 プロンプト長: 1234文字
🔧 エラー内容: 実行エラー: Traceback (most recent call last):...
💡 ヒント数: 5件

============================================================
✅ LLM応答受信
============================================================
📊 応答長: 856文字

🤖 LLMの思考プロセス:
------------------------------------------------------------
```python
import argparse
import logging
import random  # 追加

logging.basicConfig(level=logging.INFO)

def generate_password(length=12):
    """ランダムなパスワードを生成する関数"""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    password = ''
    for _ in range(length):
        password += random.choice(characters)  # 修正
    return password
...

... (残り 356文字)
------------------------------------------------------------

✅ コード抽出成功: 789文字
```

---

## 🎯 活用方法

### DBから過去のエラー解決を検索
```python
from services.db.database_manager import DatabaseManager

db = DatabaseManager()

# 成功したデバッグ履歴
cursor = db._execute_sql('''
    SELECT project_name, error_message, iterations
    FROM debug_history
    WHERE success = 1
    ORDER BY created_at DESC
    LIMIT 10
''')
```

### Web検索結果の確認
```python
# 特定のトピックの検索結果
cursor = db._execute_sql('''
    SELECT title, snippet, source
    FROM simple_search_results
    WHERE term LIKE '%Python%'
    ORDER BY confidence DESC
''')
```

### 成功パターンの再利用
```python
# 高成功率のパターン
cursor = db._execute_sql('''
    SELECT task_description, generated_code
    FROM successful_patterns
    WHERE success_rate > 0.8
    ORDER BY usage_count DESC
''')
```

---

## 📈 今後の改善

1. **Web検索結果の保存強化**
   - 現在: simple_search_resultsのみ
   - 改善: web_page_contentにページ全体を保存

2. **成功パターンの自動学習**
   - デバッグ成功時に自動的にパターンを抽出
   - 類似プロジェクトでパターンを再利用

3. **エラー解決の機械学習**
   - debug_historyから頻出エラーを分析
   - 効果的な修正方法を統計的に学習

4. **検索精度の向上**
   - Stack Overflowの直接検索
   - GitHubのissue/PRからの学習
