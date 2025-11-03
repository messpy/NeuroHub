#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
learn_light_signals.py

Nature Remo ローカルAPI 赤外線信号学習ツール
実際のリモコンから照明のON/OFF信号を学習して保存
"""

import os
import sys
import json
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# RemoローカルIP（dns-sdで取得したもの）
REMO_LOCAL_IP = "192.168.3.3"


def get_latest_signal():
    """最新の受信赤外線信号を取得"""
    try:
        url = f"http://{REMO_LOCAL_IP}/messages"
        headers = {"X-Requested-With": "curl"}

        request = Request(url, headers=headers)
        with urlopen(request, timeout=5) as response:
            signal = json.loads(response.read().decode())

        return signal

    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def send_signal(signal):
    """赤外線信号を送信"""
    try:
        url = f"http://{REMO_LOCAL_IP}/messages"
        headers = {
            "X-Requested-With": "curl",
            "Content-Type": "application/json"
        }

        data = json.dumps(signal).encode()

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request, timeout=5) as response:
            result = response.read().decode()

        print("✅ 信号送信成功")
        return True

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def learn_signal(signal_name):
    """信号を学習"""
    print(f"\n{'='*60}")
    print(f"  📡 {signal_name} 信号を学習")
    print(f"{'='*60}")

    print(f"\n🎛️ 照明のリモコンで「{signal_name}」ボタンを押してください")
    print("   Remoに向けてボタンを押すと、信号を受信します")

    input("\n準備ができたらEnterキーを押してください...")

    print("\n📡 リモコンのボタンを押してください！（5秒以内）")
    print("   ボタンを押したら、すぐにもう一度Enterキーを押してください")

    input()

    # 信号取得
    print("\n🔍 信号取得中...")
    signal = get_latest_signal()

    if signal:
        print(f"\n✅ 信号取得成功:")
        print(f"   周波数: {signal.get('freq')} kHz")
        print(f"   フォーマット: {signal.get('format')}")
        print(f"   データ長: {len(signal.get('data', []))} ポイント")

        # 信号をファイルに保存
        filename = f"light_{signal_name.lower()}.json"
        with open(filename, 'w') as f:
            json.dump(signal, f, indent=2)

        print(f"\n💾 信号を保存しました: {filename}")

        return signal
    else:
        print("\n❌ 信号取得失敗")
        return None


def test_signal(signal, signal_name):
    """学習した信号をテスト送信"""
    print(f"\n{'='*60}")
    print(f"  🧪 {signal_name} 信号をテスト送信")
    print(f"{'='*60}")

    confirm = input(f"\n学習した{signal_name}信号を送信しますか？ (y/N): ")

    if confirm.lower() == 'y':
        print(f"\n📤 {signal_name}信号送信中...")

        if send_signal(signal):
            print(f"\n💡 照明が{signal_name}しましたか？")
            return True
        else:
            print(f"\n❌ 送信失敗")
            return False
    else:
        print("スキップしました")
        return False


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  💡 Nature Remo 照明信号学習ツール")
    print("  実際のリモコンから赤外線信号を学習します")
    print("="*60)

    print(f"\n🌐 RemoローカルIP: {REMO_LOCAL_IP}")

    # 接続確認
    print("\n🔌 Remo接続確認中...")
    try:
        url = f"http://{REMO_LOCAL_IP}/messages"
        headers = {"X-Requested-With": "curl"}

        request = Request(url, headers=headers)
        with urlopen(request, timeout=5) as response:
            if response.status == 200:
                print("✅ Remo接続成功")
            else:
                print(f"⚠️ レスポンスコード: {response.status}")
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        print("\n確認事項:")
        print("  1. RemoのIPアドレスが正しいか")
        print("  2. 同じネットワークに接続しているか")
        return

    print("\n" + "="*60)
    print("  信号学習開始")
    print("="*60)

    print("\n📝 これから照明の以下のボタンを学習します:")
    print("  1. ON  - 照明を点ける")
    print("  2. OFF - 照明を消す")

    signals = {}

    # ON信号学習
    on_signal = learn_signal("ON")
    if on_signal:
        signals['on'] = on_signal
        test_signal(on_signal, "ON")

    # 3秒待機
    print("\n⏳ 3秒待機...")
    time.sleep(3)

    # OFF信号学習
    off_signal = learn_signal("OFF")
    if off_signal:
        signals['off'] = off_signal
        test_signal(off_signal, "OFF")

    # まとめ
    print("\n" + "="*60)
    print("  📊 学習結果")
    print("="*60)

    if signals:
        print(f"\n✅ {len(signals)}個の信号を学習しました:")
        for name in signals.keys():
            print(f"  - {name.upper()}: light_{name}.json")

        print("\n💡 次のステップ:")
        print("  1. 学習した信号ファイル (light_on.json, light_off.json) を確認")
        print("  2. これらの信号を使って照明を制御できます")
        print("  3. プログラムから信号を送信するには:")
        print("     python3 send_learned_signal.py on")
        print("     python3 send_learned_signal.py off")
    else:
        print("\n❌ 信号学習に失敗しました")
        print("\n💡 トラブルシューティング:")
        print("  1. リモコンの電池は十分か")
        print("  2. リモコンをRemoに近づけて試す（10cm以内）")
        print("  3. ボタンを押した直後にEnterキーを押す")

    print("\n✅ 完了")


if __name__ == "__main__":
    main()
