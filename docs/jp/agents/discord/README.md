# Discordエージェント 概要

## 🎯 役割と責任

DiscordエージェントはDiscord Botとしての機能を提供し、チャットを通じてNeuroHubの機能を利用できるようにします。

---

## 📋 主要機能

### 1. Bot Core（bot_core.py）
- Discordイベント処理
- コマンド管理
- メッセージ処理

### 2. プラグインシステム（plugin_manager.py）
- プラグイン動的ロード
- プラグイン有効化/無効化
- カスタムコマンド追加

### 3. 音声管理（voice_manager.py）
- 音声トリガー管理
- 音声合成（TTS）
- 音声認識（STT）

### 4. アンチスパム（anti_spam.py）
- スパム検出
- レート制限
- ユーザーブロック

---

## 🏗️ アーキテクチャ

```
┌─────────────────────────┐
│   Discord Bot Core      │
│                         │
│  - イベント処理         │
│  - コマンド管理         │
└──────────┬──────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐  ┌────▼────────┐
│Plugin  │  │Voice Manager│
│Manager │  │             │
└────────┘  └─────────────┘
    │             │
┌───▼─────────────▼───┐
│   LLM Agent         │
│   (AI応答生成)       │
└─────────────────────┘
```

---

## 🔧 使用方法

### Bot起動

```bash
# Discord Bot起動
python3 tools/run_discord_bot.py
```

### コマンド例

```
!help          - ヘルプ表示
!ask <質問>    - LLMに質問
!status        - Bot状態確認
!plugins       - プラグイン一覧
```

---

## ⚙️ 設定

### discord_config.yaml

```yaml
discord:
  bot_token: ${DISCORD_BOT_TOKEN}
  channel_id: ${DISCORD_CHANNEL_ID}
  command_prefix: "!"
  plugins:
    - llm_plugin
    - voice_plugin
```

### .env

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
```

---

## 📖 関連ドキュメント

- [詳細設計](./DETAILED_DESIGN.md)
- [音声管理](./VOICE_DESIGN.md)
- [その他設計](./OTHER_DESIGNS.md)

---

*最終更新: 2025年11月2日*
