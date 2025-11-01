#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音声トリガー + Ollama LLM デモ
音声で「ニューロ」などと言うとAIが応答
"""
import sys
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from services.tts.voice_trigger import VoiceTrigger
except ImportError:
    print("❌ voice_trigger.pyが見つかりません")
    print("必要なライブラリをインストールしてください:")
    print("pip install SpeechRecognition PyAudio fuzzywuzzy python-Levenshtein sounddevice numpy")
    sys.exit(1)


def ai_response(text: str, match: dict):
    """音声認識後にAIが応答"""
    print(f"\n{'='*60}")
    print(f"🎤 あなた: {text}")
    print(f"🎯 トリガー: {match['word']} (スコア: {match['score']}%)")
    print(f"{'='*60}")

    # Ollamaで応答生成
    print("\n🤖 AI が考え中...\n")

    try:
        result = subprocess.run(
            ['python', 'agents/llm_agent.py', '--test', text, '--provider', 'ollama'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=ROOT
        )

        # レスポンスを抽出
        output = result.stdout
        if 'レスポンス:' in output:
            response = output.split('レスポンス:')[1].strip()
            print(f"💬 AI: {response}\n")
        else:
            print(f"📝 AI出力:\n{output}\n")

    except Exception as e:
        print(f"❌ AI応答エラー: {e}\n")

    print(f"{'='*60}\n")


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        🎤 NeuroHub 音声AIアシスタント デモ 🤖           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

📋 トリガーワード:
   - ニューロ
   - ヘイAI
   - おしえて
   - 起動

💡 使い方:
   1. マイクに向かって話しかけてください
   2. トリガーワードが含まれるとAIが応答します
   3. Ctrl+C で終了

例:
   「ニューロ、今日の天気は？」
   「おしえて、Pythonって何？」
   「ヘイAI、1+1は？」

🔧 設定:
   - あいまい一致: 75% (発音が近ければOK)
   - 言語: 日本語
   - プロバイダー: Ollama (ローカル)

""")

    # 音声トリガー初期化
    trigger = VoiceTrigger(
        trigger_words=['ニューロ', 'ヘイAI', 'おしえて', '起動', 'AI'],
        callback=ai_response,
        language='ja-JP',
        fuzzy_threshold=75,  # ゆるめの設定で反応しやすく
        energy_threshold=3000  # 感度高め
    )

    try:
        # 音声監視開始
        trigger.start()

        # メインループ
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 終了します...\n")
        trigger.stop()

        # 統計表示
        stats = trigger.get_stats()
        print("="*60)
        print("📊 セッション統計")
        print("="*60)
        print(f"🎤 総認識回数: {stats['total_recognized']}")
        print(f"✅ トリガー回数: {stats['total_triggered']}")
        print(f"📈 トリガー率: {stats['trigger_rate']:.1f}%")

        if stats['trigger_history']:
            print("\n📜 トリガー履歴:")
            for i, h in enumerate(stats['trigger_history'], 1):
                print(f"  {i}. 「{h['text']}」→ {h['match']['word']} ({h['match']['score']}%)")

        print("="*60)
        print("\n👋 またね！\n")


if __name__ == "__main__":
    main()
