# NeuroHub Discord Bot 完全ガイド

## 🚀 セットアップ

### 1. Discord Bot作成

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリック
3. Bot名を入力（例: NeuroHub）
4. 「Bot」タブに移動
5. 「Add Bot」をクリック
6. **トークンをコピー**（Reset Token で再生成可能）

### 2. Bot権限設定

「Bot」タブで以下の権限を有効化:
- ✅ **Privileged Gateway Intents**
  - `PRESENCE INTENT`
  - `SERVER MEMBERS INTENT`
  - `MESSAGE CONTENT INTENT` ← **必須！**

「OAuth2」→「URL Generator」で以下を選択:
- **Scopes**: `bot`, `applications.commands`
- **Bot Permissions**:
  - Read Messages/View Channels
  - Send Messages
  - Manage Messages
  - Embed Links
  - Attach Files
  - Read Message History
  - Add Reactions
  - Connect（音声用）
  - Speak（音声用）
  - Use Voice Activity

生成されたURLでサーバーに招待！

### 3. トークン設定

`.env`ファイルを編集:
```env
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
```

### 4. ライブラリインストール

```bash
# Windows (PowerShell)
pip install discord.py python-dotenv gTTS PyNaCl

# Linux/WSL
pip install discord.py python-dotenv gTTS PyNaCl
```

**音声機能を使う場合:**
```bash
# FFmpegが必要（音声再生用）
# Windows: https://ffmpeg.org/download.html からダウンロード
# Linux: sudo apt install ffmpeg
```

### 5. Bot起動

```bash
python tools/run_discord_bot.py
```

---

## 📖 機能一覧

### 🔧 基本コマンド

| コマンド | 説明 | 例 |
|---------|------|-----|
| `!ping` | Bot応答速度確認 | `!ping` |
| `!info` | Bot情報表示 | `!info` |
| `!server` | サーバー情報 | `!server` |
| `!user [@user]` | ユーザー情報 | `!user @Kenny` |
| `!help_custom` | ヘルプ表示 | `!help_custom` |

### 🤖 AI・LLM機能

| コマンド | 説明 | 例 |
|---------|------|-----|
| `@NeuroHub [質問]` | AIメンション応答 | `@NeuroHub Pythonとは？` |
| `!llm [質問]` | LLMで応答生成 | `!llm 1+1は？` |
| `!knowledge [ワード]` | ナレッジベース検索 | `!knowledge Python` |
| `!knowledge_add [タイトル] [内容]` | ナレッジ追加（管理者のみ） | `!knowledge_add "Python" "プログラミング言語"` |

### 🎵 音声機能

| コマンド | 説明 | 例 |
|---------|------|-----|
| `!join` | ボイスチャンネル参加 | `!join` |
| `!leave` | ボイスチャンネル退出 | `!leave` |
| `!tts [テキスト]` | テキスト読み上げ | `!tts こんにちは` |
| `!volume [0-100]` | 音量変更 | `!volume 50` |

### 🛡️ 管理コマンド（管理者のみ）

| コマンド | 説明 | 例 |
|---------|------|-----|
| `!plugin list` | プラグイン一覧 | `!plugin list` |
| `!plugin load [name]` | プラグイン読み込み | `!plugin load my_plugin` |
| `!plugin unload [name]` | プラグイン無効化 | `!plugin unload basic_commands` |
| `!plugin reload [name]` | プラグイン再読み込み | `!plugin reload llm_commands` |
| `!whitelist add [@user]` | ホワイトリスト追加 | `!whitelist add @Kenny` |
| `!whitelist remove [@user]` | ホワイトリスト削除 | `!whitelist remove @Kenny` |
| `!blacklist add [@user]` | ブラックリスト追加 | `!blacklist add @Spammer` |
| `!blacklist remove [@user]` | ブラックリスト削除 | `!blacklist remove @Spammer` |
| `!spam_stats [@user]` | スパム統計表示 | `!spam_stats @Kenny` |

---

## 🔌 プラグインシステム

### プラグイン作成方法

1. `services/discord/plugins/` に新しい `.py` ファイルを作成
2. `PluginBase` と `commands.Cog` を継承したクラスを作成

**テンプレート:**
```python
from discord.ext import commands
from services.discord.plugin_manager import PluginBase

class MyPlugin(PluginBase, commands.Cog):
    """プラグインの説明"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "自作プラグイン"
        self.version = "1.0.0"

    @commands.command(name='mycommand')
    async def my_command(self, ctx: commands.Context):
        """コマンドの説明"""
        await ctx.send("Hello from MyPlugin!")

async def setup(bot: commands.Bot):
    await bot.add_cog(MyPlugin(bot))
```

3. `config/discord_config.yaml` の `plugins.auto_load` に追加

### 既存プラグイン

- **basic_commands.py**: 基本コマンド（ping, info, server, user）
- **llm_commands.py**: LLM連携コマンド
- **voice_commands.py**: 音声機能コマンド
- **admin_commands.py**: 管理者コマンド

---

## 🛡️ 荒らし対策機能

### 自動検出機能

- ✅ **レート制限**: 1分間のメッセージ数制限
- ✅ **重複メッセージ検出**: 同じメッセージの連投検出
- ✅ **メンションスパム**: 過剰なメンション検出
- ✅ **絵文字スパム**: 絵文字乱用検出
- ✅ **URLスパム**: URL連投検出
- ✅ **大文字スパム**: 全て大文字のメッセージ検出

### 自動対処

1. スパムメッセージを**自動削除**
2. 警告メッセージを送信（10秒後に自動削除）
3. 違反回数が閾値（デフォルト3回）を超えると**自動タイムアウト**

### カスタマイズ

`config/discord_config.yaml` で設定変更:
```yaml
anti_spam:
  max_messages_per_minute: 10  # 1分間の最大メッセージ数
  max_duplicate_messages: 3     # 同一メッセージの最大回数
  timeout_duration: 60          # タイムアウト時間（秒）
  violation_threshold: 3        # 違反回数の閾値
```

---

## 🎵 音声機能詳細

### Text-to-Speech（TTS）

**日本語読み上げ:**
```
!tts おはようございます
```

**英語読み上げ:**
```python
# voice_manager.py の text_to_speech メソッドで language='en' を指定
await bot.voice_manager.text_to_speech(guild_id, "Hello World", language='en')
```

### 音楽再生（将来拡張）

将来的に以下の機能を追加予定:
- YouTube音楽再生
- プレイリスト管理
- キュー管理
- スキップ/一時停止/再開

---

## 🤖 LLM連携

### 利用可能なLLMプロバイダー

`config/llm_config.yaml` で設定:
- **Ollama** (デフォルト): ローカルLLM
- **HuggingFace**: クラウドLLM
- **Gemini**: Google AI

### メンション応答

Botをメンションすると自動的にLLMが応答:
```
@NeuroHub Pythonの特徴を教えて
```

応答には:
- 🤖 LLM生成テキスト
- 📚 関連ナレッジベース（自動検索）

---

## 📊 データベース統合

### 自動記録

- ✅ LLM対話履歴（`llm_history`テーブル）
- ✅ Bot起動/終了イベント
- ✅ ナレッジベース検索
- ✅ コマンド実行統計

### データベース確認

```python
# Python
from services.db.database_manager import DatabaseManager
db = DatabaseManager()

# Discord関連のLLM履歴を取得
history = db.get_data('llm_history', "request_type = 'discord_mention'", limit=10)
print(history)
```

---

## 🔧 設定ファイル

### `config/discord_config.yaml`

```yaml
bot:
  prefix: "!"
  status: "NeuroHubで稼働中"

features:
  llm_enabled: true
  voice_enabled: true
  anti_spam_enabled: true

anti_spam:
  max_messages_per_minute: 10
  timeout_duration: 60

voice:
  auto_disconnect_timeout: 300
  default_volume: 0.5

plugins:
  auto_load:
    - basic_commands
    - llm_commands
```

---

## 🚀 実行例

### 基本的な使い方

```bash
# 1. Bot起動
python tools/run_discord_bot.py

# 2. Discordサーバーで
!ping
# → 🏓 Pong! レイテンシ: 50ms

!info
# → Botの詳細情報を表示

@NeuroHub Pythonとは？
# → AI応答 + 関連ナレッジ表示
```

### ボイスチャンネルで

```bash
# 1. ボイスチャンネルに参加
!join

# 2. テキスト読み上げ
!tts こんにちは、NeuroHubです

# 3. 音量調整
!volume 80

# 4. 退出
!leave
```

---

## 🛠️ トラブルシューティング

### Bot起動エラー

**エラー: `DISCORD_BOT_TOKEN が設定されていません`**
- `.env`ファイルの`DISCORD_BOT_TOKEN`を設定

**エラー: `Privileged intent provided is not enabled`**
- Discord Developer Portal で `MESSAGE CONTENT INTENT` を有効化

### 音声機能エラー

**エラー: `ffmpeg not found`**
- FFmpegをインストール: https://ffmpeg.org/download.html

**エラー: `gTTS not installed`**
- `pip install gTTS`

### コマンドが動作しない

- Botに適切な権限があるか確認
- コマンドプレフィックスが正しいか確認（デフォルト: `!`）

---

## 📝 次のステップ

### 推奨カスタマイズ

1. **プラグイン追加**: 独自機能を`services/discord/plugins/`に追加
2. **LLMプロバイダー変更**: `config/llm_config.yaml`で設定
3. **荒らし対策調整**: `config/discord_config.yaml`で閾値調整
4. **音声認識追加**: Whisperモデル統合（将来実装）

### 応用例

- **自動応答Bot**: 特定キーワードに自動返信
- **通知Bot**: 外部API連携で通知送信
- **ゲームBot**: ミニゲーム機能追加
- **モデレーションBot**: 高度な荒らし検出

---

## 📚 参考リンク

- [Discord.py公式ドキュメント](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [NeuroHub GitHub](https://github.com/messpy/NeuroHub)

---

**🎉 NeuroHub Discord Bot で楽しんでください！**
