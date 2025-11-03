#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_light_repeat.py

Nature Remo 照明制御テスト（連続送信版）
信号を複数回送信して確実に制御
"""

import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from json import loads
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo API設定
REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def get_light():
    """TAKIZUMI照明を取得"""
    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = loads(response.read().decode())

        for appliance in appliances:
            if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == 'TAKIZUMI':
                return appliance

        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def send_signal(appliance_id, button, repeat=1, interval=0.5):
    """信号を送信（繰り返し可能）"""
    results = []

    for i in range(repeat):
        try:
            url = f"{BASE_URL}appliances/{appliance_id}/light"
            headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

            data = f"button={button}".encode()

            request = Request(url, data=data, headers=headers, method='POST')
            with urlopen(request) as response:
                result = loads(response.read().decode())

            results.append(True)

            if repeat > 1:
                print(f"   {i+1}/{repeat}: ✅ 送信成功")
                if i < repeat - 1:
                    time.sleep(interval)

        except Exception as e:
            print(f"   {i+1}/{repeat}: ❌ エラー: {e}")
            results.append(False)

    return all(results)


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  💡 Nature Remo 照明制御テスト（連続送信版）")
    print("="*60)

    print(f"\n✅ API Key確認: {REMO_API_KEY[:10]}...")

    # 照明取得
    print("\n🔍 TAKIZUMI検索中...")
    light = get_light()

    if not light:
        print("❌ TAKIZUMI が見つかりません")
        return

    appliance_id = light.get('id')
    print(f"✅ 照明検出: {light.get('nickname')}")

    print("\n" + "="*60)
    print("  テスト1: ON信号を3回連続送信")
    print("="*60)

    print("\n🎛️ ON信号送信中（3回、0.5秒間隔）...")
    success_on = send_signal(appliance_id, "on", repeat=3, interval=0.5)

    if success_on:
        print("\n✅ ON信号送信完了")
        print("💡 照明が点きましたか？（5秒観察）")
    else:
        print("\n❌ ON信号送信失敗")

    time.sleep(5)

    print("\n" + "="*60)
    print("  テスト2: OFF信号を3回連続送信")
    print("="*60)

    print("\n🎛️ OFF信号送信中（3回、0.5秒間隔）...")
    success_off = send_signal(appliance_id, "off", repeat=3, interval=0.5)

    if success_off:
        print("\n✅ OFF信号送信完了")
        print("💡 照明が消えましたか？")
    else:
        print("\n❌ OFF信号送信失敗")

    print("\n" + "="*60)
    print("  テスト3: ON→待機→OFF（確実に）")
    print("="*60)

    print("\n⏳ 3秒待機...")
    time.sleep(3)

    print("\n🔆 ON信号送信中（5回、0.3秒間隔）...")
    send_signal(appliance_id, "on", repeat=5, interval=0.3)

    print("\n💡 照明が点きましたか？（10秒観察）")
    time.sleep(10)

    print("\n🌙 OFF信号送信中（5回、0.3秒間隔）...")
    send_signal(appliance_id, "off", repeat=5, interval=0.3)

    print("\n💡 照明が消えましたか？")

    print("\n" + "="*60)
    print("  ✅ テスト完了")
    print("="*60)

    print("\n📊 実行結果:")
    print("   テスト1 (ON×3): " + ("✅ 成功" if success_on else "❌ 失敗"))
    print("   テスト2 (OFF×3): " + ("✅ 成功" if success_off else "❌ 失敗"))

    print("\n💡 どのテストで照明が反応しましたか？")
    print("   1. ON×3で点いた")
    print("   2. OFF×3で消えた")
    print("   3. ON×5で点いた")
    print("   4. OFF×5で消えた")
    print("   5. どれも反応しなかった")


if __name__ == "__main__":
    main()
