#!/usr/bin/env python3
import pyopenjtalk, soundfile as sf, subprocess, tempfile, os, sys, argparse

def speak(text: str, sync: bool = False):
    """指定テキストを音声合成して再生。sync=Trueなら再生完了まで待機。"""
    if not text.strip():
        print("[info] 空の入力はスキップします。")
        return
    x, sr = pyopenjtalk.tts(text)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, x, sr)
    cmd = ["mpv", "--no-video", "--really-quiet", tmp.name]
    if sync:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[ok] 『{text}』を{'同期' if sync else '非同期'}再生しました。")
    if sync:
        os.unlink(tmp.name)  # 同期再生は再生後削除
    else:
        # 非同期の場合はmpv側終了後に自動削除できないため放置（必要ならtmp監視で削除）
        pass

def interactive(sync: bool):
    """対話モード"""
    print("=== 日本語音声合成 (pyopenjtalk) ===")
    print("テキストを入力してください（空で終了）")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[終了]")
            break
        if not text:
            print("[終了]")
            break
        speak(text, sync=sync)

def main():
    parser = argparse.ArgumentParser(description="日本語TTS（pyopenjtalk + mpv）")
    parser.add_argument("text", nargs="*", help="再生するテキスト（空なら対話モード）")
    parser.add_argument("--sync", action="store_true", help="同期再生モード（再生完了まで待つ）")
    args = parser.parse_args()

    if args.text:
        text = " ".join(args.text)
        speak(text, sync=args.sync)
    else:
        interactive(sync=args.sync)

if __name__ == "__main__":
    main()
