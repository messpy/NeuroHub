# Discord Bot コマンドテスト手順

Discord Botが起動しました。以下のコマンドをDiscordチャンネルでテストしてください。

## 📋 基本コマンドテスト

### 1. Bot応答確認
```
!ping
!info
!help
```

### 2. Nature Remo制御テスト

**ヘルプ表示**:
```
!remo
```

**家電一覧**:
```
!remo devices
```

**照明ON** (TAKIZUMI):
```
!remo light on
```

**照明OFF**:
```
!remo light off
```

**別の照明** (例):
```
!remo light on 別の照明名
```

### 3. ユーザー情報テスト

**自分のアバター**:
```
!avatar
```

**他のユーザーのアバター**:
```
!avatar @ユーザー名
```

**ユーザー詳細情報**:
```
!userinfo
!userinfo @ユーザー名
```

### 4. Ollama LLMテスト

**質問**:
```
!ask Pythonでファイルを読み込む方法は？
```

**チャット**:
```
!chat こんにちは！
```

### 5. サーバー情報テスト

```
!serverinfo
!members
```

### 6. ボイスチャンネルテスト

1. ボイスチャンネルに参加
2. 通知チャンネル（DISCORD_NOTIFICATION_CHANNEL_ID）で参加通知確認
3. ボイスチャンネルから退出
4. 退出通知と滞在時間確認

---

## 🔍 トラブルシューティング

### コマンドが反応しない場合

1. **Botが起動しているか確認**:
   - WSLターミナルでログ確認
   - 起動通知がログチャンネルに届いているか

2. **コマンドプレフィックス確認**:
   - `!`を忘れていないか確認

3. **権限確認**:
   - Botがチャンネルにアクセス権限を持っているか
   - メッセージ送信権限があるか

4. **エラーログ確認**:
   - WSLターミナルでエラーメッセージを確認

### Nature Remo制御が動かない場合

1. **REMO_API確認**:
   ```bash
   cat .env | grep REMO_API
   ```

2. **デバイス名確認**:
   - `!remo devices`で正しい名前を確認
   - デフォルトは`TAKIZUMI`

3. **主電源確認**:
   - Nature Remoデバイスの電源がON
   - Wi-Fi接続確認

### LLMが応答しない場合

1. **Ollama起動確認**:
   ```bash
   ollama list
   ```

2. **モデル確認**:
   ```bash
   ollama run gemma2:2b
   ```

---

## 📊 期待される結果

### 起動通知
- ログチャンネル（ID: 1005826751391342663）に起動Embedメッセージ
- サーバー数、プラグイン数、起動時刻表示

### Nature Remo制御
- `!remo devices`: 家電一覧表示（6個: TAKIZUMI, エアコン2個, 扇風機, テレビ, セロリ）
- `!remo light on`: 照明ON成功メッセージ
- `!remo light off`: 照明OFF成功メッセージ

### ボイスチャンネル
- 参加時: 緑色Embedメッセージ（🎤 ボイスチャンネル参加）
- 退出時: 赤色Embedメッセージ（👋 ボイスチャンネル退出 + 滞在時間）

### LLM応答
- `!ask`: 質問に対する回答（緑色Embed）
- `!chat`: チャット応答（青色Embed）

---

## 🐛 既知の問題

### test_plugin.py ロードエラー
```
ERROR: The command ping is already an existing command or alias.
```

**原因**: `basic_commands.py`にも`ping`コマンドが存在

**影響**: test_pluginの他のコマンド（hello, info, status, notify）も使用不可

**回避策**: 既存の`!info`コマンドを使用

---

## 📝 テスト結果記録

### Nature Remo API（直接テスト）
- ✅ 家電一覧取得: 6個成功
- ✅ TAKIZUMI検出: 成功
- ✅ ON制御: 成功
- ✅ OFF制御: 成功

### Discord Bot
- ✅ 起動: 成功
- ✅ 起動通知送信: 成功
- ✅ プラグインロード: 8個成功
- ✅ コマンド登録: 36個

### 未テスト項目
- [ ] `!remo`コマンド応答
- [ ] `!remo devices`実行
- [ ] `!remo light on/off`実行
- [ ] ボイスチャンネル通知
- [ ] `!avatar`, `!userinfo`実行
- [ ] `!ask`, `!chat`実行
- [ ] `!serverinfo`, `!members`実行

---

Discordチャンネルでコマンドをテストして結果を教えてください！
