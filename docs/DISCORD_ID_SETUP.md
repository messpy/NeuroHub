# Discord Bot 設定完全ガイド - ID取得方法

## 🆔 Discord ID の取得方法

### 1. 開発者モードを有効化

**PCの場合:**
1. Discordアプリで「設定」⚙️をクリック
2. 左側メニューで「詳細設定」を選択
3. 「開発者モード」をONにする

**スマホの場合:**
1. Discordアプリで右下の「設定」をタップ
2. 「動作・外観」をタップ
3. 「開発者モード」をONにする

### 2. 各種IDの取得

#### 👤 User ID（ユーザーID）の取得

**自分のUser ID:**
1. 任意のチャンネルで自分の名前をクリック
2. 「IDをコピー」をクリック
3. 数字の羅列（例: `123456789012345678`）がコピーされる

**他のユーザーのUser ID:**
1. そのユーザーの名前を右クリック
2. 「IDをコピー」をクリック

#### 🏠 Guild ID（サーバーID）の取得

1. サーバーアイコンを右クリック
2. 「IDをコピー」をクリック

#### 📝 Channel ID（チャンネルID）の取得

1. チャンネル名を右クリック
2. 「IDをコピー」をクリック

### 3. .envファイルの設定例

```env
# Discord Bot Token
DISCORD_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE

# 管理者設定（実際のIDに置き換え）
DISCORD_ADMIN_USER_IDS=123456789012345678,987654321098765432
DISCORD_ADMIN_USERNAMES=kenny,admin_user

# サーバー・チャンネル設定
DISCORD_MAIN_GUILD_ID=876543210987654321
DISCORD_LOG_CHANNEL_ID=111111111111111111
DISCORD_NOTIFICATION_CHANNEL_ID=222222222222222222
```

---

## 🤖 Bot Token の取得方法

### 1. Discord Developer Portal でアプリケーション作成

1. https://discord.com/developers/applications にアクセス
2. 「New Application」をクリック
3. Bot名を入力（例: NeuroHub）
4. 「Create」をクリック

### 2. Bot の作成

1. 左側メニューで「Bot」をクリック
2. 「Add Bot」をクリック
3. 「Yes, do it!」をクリック

### 3. Token の取得

1. 「Token」セクションで「Reset Token」をクリック
2. 「Yes, do it!」をクリック
3. 表示されたトークンをコピー（**重要: 一度だけ表示**）
4. `.env`ファイルの`DISCORD_BOT_TOKEN`に貼り付け

⚠️ **注意**: トークンは**絶対に他人に見せない**でください！

### 4. Bot 権限の設定

**必須権限（Bot タブ）:**
- ✅ `PRESENCE INTENT`
- ✅ `SERVER MEMBERS INTENT`
- ✅ `MESSAGE CONTENT INTENT` ← **超重要！**

**Bot権限（OAuth2 → URL Generator）:**
- Scopes: `bot`, `applications.commands`
- Bot Permissions:
  - ✅ Read Messages/View Channels
  - ✅ Send Messages
  - ✅ Manage Messages
  - ✅ Embed Links
  - ✅ Attach Files
  - ✅ Read Message History
  - ✅ Add Reactions
  - ✅ Connect（音声用）
  - ✅ Speak（音声用）
  - ✅ Use Voice Activity
  - ✅ Manage Roles（リアクションロール用）

### 5. サーバーに招待

1. OAuth2 → URL Generator で生成されたURLをコピー
2. URLにアクセス
3. 招待するサーバーを選択
4. 「認証」をクリック

---

## 🔧 設定のテスト方法

### 1. 基本テスト

```bash
# Bot起動
python tools/run_discord_bot.py

# Discordで確認
!ping  # Bot応答テスト
!info  # Bot情報表示
```

### 2. 管理者権限テスト

```bash
# 管理者のみ使用可能
!plugin list
!whitelist add @ユーザー
```

### 3. ID設定確認

```bash
# Bot起動時のログを確認
# "👑 管理者ID: ['123456789012345678']" が表示されればOK
```

---

## 🆔 ID の例と確認方法

### ID の形式
- User ID: `123456789012345678` (18桁の数字)
- Guild ID: `876543210987654321` (18桁の数字)
- Channel ID: `111111111111111111` (18桁の数字)

### ID が正しく設定されているか確認

```python
# Pythonで確認
import os
from dotenv import load_dotenv

load_dotenv()

print("管理者ID:", os.getenv('DISCORD_ADMIN_USER_IDS'))
print("サーバーID:", os.getenv('DISCORD_MAIN_GUILD_ID'))
print("ログチャンネルID:", os.getenv('DISCORD_LOG_CHANNEL_ID'))
```

---

## ❓ よくある問題

### ❌ "MESSAGE CONTENT INTENT が無効"
- Discord Developer Portal → Bot → Privileged Gateway Intents で有効化

### ❌ "Bot Token が無効"
- Tokenが正しくコピーされているか確認
- `.env`ファイルに余分なスペースがないか確認

### ❌ "管理者コマンドが使えない"
- User IDが正しく設定されているか確認
- `.env`ファイルの再読み込み（Bot再起動）

### ❌ "チャンネルIDが見つからない"
- Botがそのチャンネルにアクセス権限があるか確認
- Channel IDが正しいか確認

---

## 🎯 推奨設定例

### 小規模サーバー（個人用）
```env
DISCORD_ADMIN_USER_IDS=あなたのUser ID
DISCORD_ADMIN_USERNAMES=あなたのユーザー名
DISCORD_MAIN_GUILD_ID=サーバーID
DISCORD_LOG_CHANNEL_ID=ログ用チャンネルID
DISCORD_NOTIFICATION_CHANNEL_ID=通知用チャンネルID
```

### 大規模サーバー（複数管理者）
```env
DISCORD_ADMIN_USER_IDS=管理者1,管理者2,管理者3
DISCORD_ADMIN_USERNAMES=admin1,admin2,admin3
DISCORD_MAIN_GUILD_ID=メインサーバーID
DISCORD_LOG_CHANNEL_ID=管理者専用ログチャンネルID
DISCORD_NOTIFICATION_CHANNEL_ID=一般通知チャンネルID
```

---

**🎉 設定完了後、Botを再起動してテストしてください！**
