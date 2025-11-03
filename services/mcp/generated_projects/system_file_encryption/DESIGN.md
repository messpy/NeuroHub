# system_file_encryption 設計書

## 1. プロジェクト概要
本プロジェクトは、ユーザーがログインして開発環境にファイルを保存するための暗号化システムを作成します。

## 2. 機能仕様
- **基本機能**：
  - 用户のログイン情報やファイル名を暗号化します。
  - ファイル名を暗号化後、ファイルを安全な場所に保存します。

- **エラーハンドリング**：
  - 一般的な错误处理と警告を含むエラーログを保持する方法を提案しています。

- **ヘルプ機能**：
  - オリジナルのログイン画面やファイル入力画面を提供し、使用者の質問に回答します。
  
## 3. インターフェース設計 (IF)
### 入力インターフェース
- コマンドライン引数：ユーザーが命令行でファイル名やパスを指定する場合があります。

```bash
python system_file_encryption.py [user_name] [file_path]
```

```ini
[general]
# 個別入力（デフォルト）
# ファイル名は、ユーザーユーザーにユーザーに付けてください。パスを指定して下さい。

[user_id]
# ファイル名を指定する値。
file_name = system_file_encryption
```

### 出力インターフェース  
- 標準出力（結果）
- 標準エラー（エラー）

```bash
python system_file_encryption.py
```

```ini
[general]
# リストのエラーと警告。
file_not_found = デフォルトのファイル名が見つからない
password_error = 密码が誤りです

[user_id]
# ファイル名を指定する値。
file_name = file_to_be_encrypted
```

## 4. 応答情報仕様
### 正常ケース
- 正しい入力で期待結果を出力
- 処理時間5秒以内

```bash
python system_file_encryption.py example.txt /home/user/documents/example.txt
```

```ini
[general]
file_name = example.txt
```

```bash
python system_file_encryption.py
```

```ini
[general]
file_name = file_to_be_encrypted
```

### エラー応答
- パスの指定が不正であることを示すエラーログを含む。
- クラッシュなし

```bash
python system_file_encryption.py /does_not_exist.txt /path/to/file_to_be_encrypted
```

```ini
[general]
file_name = file_to_be_encrypted
```

```bash
python system_file_encryption.py
```

```ini
[general]
file_name = デフォルトのファイル名
password_error = 密码が誤りです
```

## 5. 期待値定義
### 正常ケース
- 正しい入力で期待結果を出力
- 処理時間5秒以内

```bash
python system_file_encryption.py example.txt /home/user/documents/example.txt
```

```ini
[general]
file_name = example.txt
```

```bash
python system_file_encryption.py
```

```ini
[general]
file_name = file_to_be_encrypted
```

### エラーケース
- パスの指定が不正であることを示すエラーログを含む。
- クラッシュなし

```bash
python system_file_encryption.py /does_not_exist.txt /path/to/file_to_be_encrypted
```

```ini
[general]
file_name = file_to_be_encrypted
```

```bash
python system_file_encryption.py
```

```ini
[general]
file_name = デフォルトのファイル名
password_error = 寶りのパスワードが誤っていた
```

## 6. 常用情報
- **Python**: Pythonは、最も普及しているコード言語です。また、開発者にも人気があります。
- **アルファベット`: ``**: すべての基本的な要素と関数を含めています。


以上の設計書をご覧いただきありがとうございます。