# 音声トリガーシステム使用ガイド

## 📖 概要

マイクから音声を拾って特定の単語に反応する高精度な音声認識システムです。

### ✨ 特徴

- **高精度認識**: Google Speech Recognition API使用
- **あいまいマッチング**: 発音が近ければ自動補正
- **カスタマイズ可能**: トリガーワード、閾値、言語を自由に設定
- **ローカル動作**: 外部サーバー不要（Googleのみオンライン）
- **統計機能**: 認識率、トリガー履歴を記録

## 🚀 セットアップ

### 1. 必要なライブラリをインストール

```bash
pip install SpeechRecognition PyAudio fuzzywuzzy python-Levenshtein sounddevice numpy
```

**Windows環境でPyAudioのインストールエラーが出る場合:**

```bash
# pipwin経由でインストール
pip install pipwin
pipwin install pyaudio
```

または、[非公式ホイール](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)からダウンロード

### 2. マイクテスト

```bash
python services/tts/voice_trigger.py --test-mic
```

## 📝 基本的な使い方

### デフォルト設定で起動

```bash
python services/tts/voice_trigger.py
```

デフォルトトリガーワード: `こんにちは`, `起動`, `ニューロハブ`

### カスタムトリガーワードで起動

```bash
# 1つの単語
python services/tts/voice_trigger.py --words "ヘイSiri"

# 複数の単語
python services/tts/voice_trigger.py --words "OK Google" "アレクサ" "コルタナ"
```

### 言語を変更

```bash
# 英語
python services/tts/voice_trigger.py --language en-US --words "hello" "start" "wake up"

# 中国語
python services/tts/voice_trigger.py --language zh-CN --words "你好" "启动"
```

### あいまいマッチング閾値を調整

```bash
# 厳密なマッチング（90%以上）
python services/tts/voice_trigger.py --threshold 90 --words "ニューロハブ"

# ゆるいマッチング（70%以上）- 発音が曖昧でもOK
python services/tts/voice_trigger.py --threshold 70 --words "起動"
```

### 音量閾値を調整

```bash
# 静かな環境（感度高）
python services/tts/voice_trigger.py --energy 2000

# うるさい環境（感度低）
python services/tts/voice_trigger.py --energy 6000
```

## 💾 設定の保存と読み込み

### 設定を保存

```bash
python services/tts/voice_trigger.py --words "起動" "ニューロハブ" --threshold 85 --save
```

設定は `config/voice_trigger_config.json` に保存されます

### 保存した設定を読み込み

```bash
python services/tts/voice_trigger.py --load
```

## 🎯 使用例

### 例1: 音声でプログラム起動

```python
from services.tts.voice_trigger import VoiceTrigger
import subprocess

def launch_app(text, match):
    if match['word'] == '起動':
        print("アプリケーションを起動します...")
        subprocess.run(['python', 'your_app.py'])
    elif match['word'] == '終了':
        print("システムを終了します...")
        exit(0)

trigger = VoiceTrigger(
    trigger_words=['起動', '終了'],
    callback=launch_app,
    fuzzy_threshold=85
)

trigger.start()
```

### 例2: Ollama LLMと連携

```python
from services.tts.voice_trigger import VoiceTrigger
import subprocess

def talk_to_llm(text, match):
    print(f"\n💬 あなた: {text}")

    # Ollamaで応答生成
    result = subprocess.run(
        ['python', 'agents/llm_agent.py', '--test', text, '--provider', 'ollama'],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    print(f"🤖 AI: {result.stdout}")

trigger = VoiceTrigger(
    trigger_words=['ニューロ', 'AI', 'おしえて'],
    callback=talk_to_llm,
    fuzzy_threshold=75
)

trigger.start()

# メインループ
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    trigger.stop()
```

### 例3: 音声でGitコミット

```python
from services.tts.voice_trigger import VoiceTrigger
import subprocess

def git_commit_voice(text, match):
    if 'コミット' in text:
        # 音声からコミットメッセージを抽出
        message = text.replace('コミット', '').strip()
        print(f"📝 コミットメッセージ: {message}")

        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', message])
        print("✅ コミット完了")

trigger = VoiceTrigger(
    trigger_words=['コミット'],
    callback=git_commit_voice,
    fuzzy_threshold=80
)

trigger.start()
```

## ⚙️ 設定パラメータ

| パラメータ | デフォルト | 説明 |
|-----------|----------|------|
| `--words` | こんにちは, 起動, ニューロハブ | トリガーワード |
| `--language` | ja-JP | 認識言語 |
| `--threshold` | 80 | あいまい一致閾値 (0-100) |
| `--energy` | 4000 | 音量閾値（高いほど大きい声が必要） |
| `--save` | - | 設定を保存 |
| `--load` | - | 設定を読み込み |
| `--test-mic` | - | マイクテスト |

## 🎤 対応言語

- **日本語**: `ja-JP`
- **英語（米国）**: `en-US`
- **英語（英国）**: `en-GB`
- **中国語（簡体字）**: `zh-CN`
- **韓国語**: `ko-KR`
- **スペイン語**: `es-ES`
- **フランス語**: `fr-FR`
- **ドイツ語**: `de-DE`

[対応言語一覧](https://cloud.google.com/speech-to-text/docs/languages)

## 🔧 トラブルシューティング

### マイクが認識されない

```bash
# 利用可能なマイクデバイスを確認
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

### 認識精度が低い

1. **音量閾値を調整**: `--energy` パラメータを変更
2. **あいまい閾値を下げる**: `--threshold 70` など
3. **環境ノイズを減らす**: 静かな場所で使用
4. **マイクの位置を調整**: 口元に近づける

### PyAudioインストールエラー（Windows）

```bash
# Microsoft C++ Build Toolsをインストール
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# または pipwin を使用
pip install pipwin
pipwin install pyaudio
```

## 📊 統計情報

プログラム終了時（Ctrl+C）に以下の統計が表示されます:

- 総認識回数
- トリガー回数
- トリガー率
- 最近のトリガー履歴

## 🚀 応用例

### スマートホーム制御

```python
trigger_words = ['電気つけて', '電気消して', '温度上げて', '温度下げて']
```

### 音声メモ

```python
def save_memo(text, match):
    with open('memo.txt', 'a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
```

### リマインダー

```python
def set_reminder(text, match):
    # 「1時間後にリマインド」など
    # 時間を解析して通知をセット
    pass
```

---

**NeuroHub Voice Trigger System** - 高精度・カスタマイズ可能な音声認識
