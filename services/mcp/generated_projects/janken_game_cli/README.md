# Janken Game CLI - じゃんけんゲーム

SQLiteデータベースを使用した本格的なじゃんけんゲームCLIアプリケーション

## 🎮 機能

- ✅ ユーザー登録・管理
- ✅ じゃんけん対戦（グー・チョキ・パー）
- ✅ 勝敗判定・記録
- ✅ ユーザー統計情報表示（勝率、戦績）
- ✅ 対戦履歴表示
- ✅ ランキング表示（勝率順）

## 📋 必要要件

- Python 3.12+
- SQLite3（Pythonに標準付属）

## 🚀 セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd janken_game_cli

# 実行権限付与（Linuxの場合）
chmod +x janken_game_cli.py
```

## 💻 使い方

### 1. ユーザー登録

```bash
python3 janken_game_cli.py register --username kenny
```

**出力例:**
```
ユーザー 'kenny' を登録しました。
```

### 2. じゃんけん対戦

```bash
# グーで勝負
python3 janken_game_cli.py play --username kenny --choice rock

# パーで勝負
python3 janken_game_cli.py play --username kenny --choice paper

# チョキで勝負
python3 janken_game_cli.py play --username kenny --choice scissors
```

**出力例:**
```
あなた: グー | コンピューター: チョキ
結果: 🎉 勝ち！
```

### 3. 統計情報表示

```bash
python3 janken_game_cli.py stats --username kenny
```

**出力例:**
```
=== kenny の統計 ===
総試合数: 11
勝利: 2
敗北: 3
引き分け: 6
勝率: 18.2%
```

### 4. 対戦履歴表示

```bash
# 最新10件表示（デフォルト）
python3 janken_game_cli.py history --username kenny

# 最新5件表示
python3 janken_game_cli.py history --username kenny --limit 5
```

**出力例:**
```
=== kenny の対戦履歴 (最新5件) ===
🤝 paper vs paper | 2025-11-02 12:03:29
🤝 paper vs paper | 2025-11-02 12:03:28
😢 paper vs scissors | 2025-11-02 12:03:28
🎉 paper vs rock | 2025-11-02 12:03:27
🤝 rock vs rock | 2025-11-02 12:03:26
```

### 5. ランキング表示

```bash
# 上位10名表示（デフォルト）
python3 janken_game_cli.py ranking

# 上位5名表示
python3 janken_game_cli.py ranking --limit 5
```

**出力例:**
```
=== ランキング (上位3名) ===
順位    ユーザー名          勝率        勝利数     総試合数
------------------------------------------------------------
1     bob            37.5%   3       8
2     alice          20.0%   3       15
3     kenny          18.2%   2       11
```

## 🎯 選択肢

| 選択肢 | 英語名 | 日本語名 |
|--------|--------|----------|
| rock | グー | ✊ |
| paper | パー | ✋ |
| scissors | チョキ | ✌️ |

## 🧪 テスト

```bash
# テスト実行
python3 -m pytest test_janken_game.py -v

# カバレッジ付きテスト
python3 -m pytest test_janken_game.py -v --cov=janken_game_cli
```

**テスト結果:**
```
16 passed in 4.86s ✅
```

### テスト内容

- ✅ データベース初期化テスト
- ✅ ユーザー登録テスト
- ✅ 重複ユーザー検証テスト
- ✅ じゃんけんロジックテスト（勝利・敗北・引き分け）
- ✅ 統計計算テスト
- ✅ 履歴取得テスト
- ✅ ランキングテスト
- ✅ 統合テスト（全体フロー）

## 📁 ファイル構成

```
janken_game_cli/
├── janken_game_cli.py      # メインプログラム
├── test_janken_game.py     # テストコード
├── README.md               # このファイル
├── requirements.txt        # 依存関係（開発用）
└── janken_game.db          # データベース（自動生成）
```

## 🗄️ データベース設計

### usersテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | ユーザーID |
| username | TEXT | NOT NULL UNIQUE | ユーザー名 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 登録日時 |

### user_statsテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| user_id | INTEGER | PRIMARY KEY REFERENCES users(id) | ユーザーID |
| total_games | INTEGER | DEFAULT 0 | 総試合数 |
| wins | INTEGER | DEFAULT 0 | 勝利数 |
| losses | INTEGER | DEFAULT 0 | 敗北数 |
| draws | INTEGER | DEFAULT 0 | 引き分け数 |
| win_rate | REAL | DEFAULT 0.0 | 勝率(%) |

### game_historyテーブル

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 履歴ID |
| user_id | INTEGER | REFERENCES users(id) | ユーザーID |
| user_choice | TEXT | NOT NULL | ユーザーの選択 |
| computer_choice | TEXT | NOT NULL | コンピューターの選択 |
| result | TEXT | NOT NULL | 結果 |
| played_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | プレイ日時 |

## 🔒 セキュリティ

- ✅ SQLインジェクション対策（プレースホルダー使用）
- ✅ 入力値検証（選択肢チェック）
- ✅ エラーハンドリング実装

## 🐛 トラブルシューティング

### ユーザーが見つからない

```bash
# エラー
ユーザー 'username' が見つかりません。register コマンドで登録してください。

# 解決方法
python3 janken_game_cli.py register --username username
```

### 重複ユーザー名

```bash
# エラー
エラー: ユーザー名 'username' は既に使用されています。

# 解決方法
別のユーザー名を使用してください
```

### 無効な選択

```bash
# エラー
無効な選択です。rock, paper, scissors から選んでください。

# 解決方法
rock, paper, scissors のいずれかを指定してください
```

## 📝 使用例スクリプト

```bash
# ユーザー登録
python3 janken_game_cli.py register --username alice
python3 janken_game_cli.py register --username bob

# 対戦
for i in {1..10}; do
    python3 janken_game_cli.py play --username alice --choice rock
done

for i in {1..10}; do
    python3 janken_game_cli.py play --username bob --choice paper
done

# ランキング確認
python3 janken_game_cli.py ranking
```

## 🌟 技術スタック

- **言語**: Python 3.12
- **データベース**: SQLite3
- **ライブラリ**:
  - argparse: CLI引数解析
  - sqlite3: データベース操作
  - random: コンピューターの手生成
  - datetime: タイムスタンプ管理
  - pytest: テストフレームワーク

## 📄 ライセンス

MIT License

## 👤 作者

NeuroHub Team

## 🙏 謝辞

このプロジェクトはNeuroHub MCPシステムによって自動生成されました。

---

**楽しいじゃんけんライフを！** 🎮✨
