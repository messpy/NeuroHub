# Discord Bot VC文字起こし機能ガイド

## 📋 概要

NeuroHub Discord Botの**VC（ボイスチャンネル）文字起こし機能**は、ボイスチャンネルでの会話を自動的に録音し、AIで文字起こしを行う機能です。

## 🎯 主な機能

1. **VC参加・録音**
   - コマンド一つでボイスチャンネルに参加
   - 自動的に音声録音開始

2. **文字起こし**
   - OpenAI Whisper API（高精度、有料）
   - faster-whisper（ローカル実行、無料）
   - 日本語対応

3. **ログ保存**
   - 文字起こし結果を自動保存
   - タイムスタンプ付き
   - ユーザー別に整理

## 🚀 使い方

### 基本的な使い方

#### 1. VCに参加して録音開始

```
!vc_join
```

または短縮形：
```
!vcjoin
!vj
```

**手順**:
1. 自分が先にボイスチャンネルに接続
2. コマンドを実行
3. Botが同じVCに参加して録音開始

#### 2. VCから退出して文字起こし実行

```
!vc_leave
```

または短縮形：
```
!vcleave
!vl
```

**処理**:
1. 録音を停止
2. 音声データを処理
3. Whisper APIで文字起こし
4. 結果をチャンネルに投稿
5. ログファイルに保存

#### 3. 過去のログを確認

```
!vc_logs
```

最新5件のログを表示。件数指定も可能：
```
!vc_logs 10
```

## 🔧 セットアップ

### 必須パッケージインストール

#### 方法1: OpenAI Whisper API（高精度、有料）

```bash
# OpenAI APIパッケージ
pip install openai>=1.0.0

# .envファイルにAPI Keyを追加
OPENAI_API_KEY=sk-your-api-key-here
```

**利点**:
- ✅ 高精度な文字起こし
- ✅ 多言語対応
- ✅ サーバー負荷なし

**欠点**:
- ❌ 使用量に応じて課金
- ❌ インターネット接続必須

#### 方法2: faster-whisper（ローカル、無料）

```bash
# faster-whisperパッケージ
pip install faster-whisper>=0.10.0

# または openai-whisper（より高精度だが遅い）
pip install openai-whisper>=20231117
```

**利点**:
- ✅ 完全無料
- ✅ オフライン動作可能
- ✅ プライバシー保護

**欠点**:
- ❌ サーバー負荷が高い
- ❌ 初回実行時にモデルダウンロード（~1GB）

### 推奨構成

```bash
# 基本パッケージ（必須）
pip install discord.py[voice]>=2.3.0
pip install PyNaCl>=1.5.0

# 文字起こしエンジン（どちらか必須）
pip install faster-whisper>=0.10.0  # 無料・ローカル
# または
pip install openai>=1.0.0  # 有料・クラウド
```

## 📊 文字起こし結果の例

### チャンネル投稿

```
🎤 音声文字起こし結果
合計 3 件の音声

1. ユーザーA
```
こんにちは、今日の会議を始めます。
議題は新機能の実装についてです。
```

2. ユーザーB
```
了解しました。まず要件定義から
進めていきましょう。
```

3. ユーザーC
```
データベース設計も並行して
進めたいと思います。
```
```

### ログファイル

保存場所: `logs/vc_transcripts/transcript_{guild_id}_{timestamp}.txt`

```
VC文字起こしログ
サーバーID: 1234567890
日時: 2025-11-03T12:34:56

======================================================================

ユーザー: ユーザーA
時刻: 2025-11-03T12:34:56
内容:
こんにちは、今日の会議を始めます。
議題は新機能の実装についてです。

----------------------------------------------------------------------

ユーザー: ユーザーB
時刻: 2025-11-03T12:35:12
内容:
了解しました。まず要件定義から進めていきましょう。

----------------------------------------------------------------------
```

## 🎨 コマンド一覧

| コマンド | 短縮形 | 説明 |
|---------|-------|------|
| `!vc_join` | `!vcjoin`, `!vj` | VC参加・録音開始 |
| `!vc_leave` | `!vcleave`, `!vl` | VC退出・文字起こし実行 |
| `!vc_logs` | `!vclogs` | 過去のログ表示 |

## ⚙️ 設定

### Whisperモデルの変更

`services/discord/plugins/vc_transcription.py` の以下の行を編集：

```python
# デフォルト: base（高速・低精度）
self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

# より高精度（遅い）
self.whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")

# 最高精度（非常に遅い）
self.whisper_model = WhisperModel("large", device="cpu", compute_type="int8")
```

### GPUを使用（高速化）

```python
# NVIDIA GPU使用（CUDA対応GPUが必要）
self.whisper_model = WhisperModel("base", device="cuda", compute_type="float16")
```

## 🔒 プライバシーとセキュリティ

### ログ保存場所

- 保存先: `logs/vc_transcripts/`
- ファイル名: `transcript_{サーバーID}_{タイムスタンプ}.txt`
- 自動削除: なし（手動削除が必要）

### 注意事項

1. **録音の同意を得る**
   - VC参加者全員に録音の事実を通知
   - 同意を得てから録音開始

2. **ログの取り扱い**
   - 機密情報が含まれる可能性あり
   - 適切に管理・削除

3. **API Keyの管理**
   - `.env`ファイルは`.gitignore`に追加
   - GitHub等に公開しない

## 🐛 トラブルシューティング

### 問題1: Botが音声を録音しない

**原因**:
- discord.py[voice]がインストールされていない
- PyNaClがインストールされていない

**解決策**:
```bash
pip install discord.py[voice]
pip install PyNaCl
```

### 問題2: 文字起こしが実行されない

**原因**:
- Whisperがインストールされていない
- OpenAI API Keyが未設定

**解決策**:
```bash
# ローカル実行の場合
pip install faster-whisper

# OpenAI API使用の場合
# .envファイルに追加
OPENAI_API_KEY=sk-your-key
```

### 問題3: 文字起こし精度が低い

**原因**:
- モデルサイズが小さい（`base`）
- 音質が悪い

**解決策**:
```python
# より大きいモデルを使用
WhisperModel("medium", ...)  # または "large"
```

### 問題4: 処理が遅い

**原因**:
- CPUで実行している
- モデルサイズが大きい

**解決策**:
```python
# GPUを使用（CUDA対応GPU必須）
WhisperModel("base", device="cuda", compute_type="float16")
```

## 📈 パフォーマンス比較

| モデル | 精度 | 速度 | メモリ使用量 |
|--------|------|------|-------------|
| tiny | ⭐⭐ | ⚡⚡⚡⚡⚡ | ~1 GB |
| base | ⭐⭐⭐ | ⚡⚡⚡⚡ | ~1 GB |
| small | ⭐⭐⭐⭐ | ⚡⚡⚡ | ~2 GB |
| medium | ⭐⭐⭐⭐⭐ | ⚡⚡ | ~5 GB |
| large | ⭐⭐⭐⭐⭐ | ⚡ | ~10 GB |

推奨: **base**（バランスが良い）

## 🚀 今後の拡張

- [ ] リアルタイム文字起こし（ストリーミング）
- [ ] 話者識別機能
- [ ] 感情分析
- [ ] 自動要約
- [ ] 多言語対応強化
- [ ] Discord埋め込み（Embed）での結果表示改善

## 📝 関連ドキュメント

- [Discord Bot実装ガイド](DISCORD_BOT_GUIDE.md)
- [Nature Remo連携](DISCORD_BOT_IMPLEMENTATION_REPORT.md)
- [Whisper公式ドキュメント](https://github.com/openai/whisper)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)

---

*最終更新: 2025年11月3日*
