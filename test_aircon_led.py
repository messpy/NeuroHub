#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_aircon_led.py

エアコン操作でRemoランプ点滅を確認
"""

import os
import time
from urllib.request import urlopen, Request
from json import loads, dumps
from dotenv import load_dotenv

load_dotenv()

REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def test_aircon():
    """エアコンON操作でランプ点滅確認"""
    print("\n" + "="*70)
    print("  🌡️ エアコンON操作テスト（Remoランプ点滅確認）")
    print("="*70)

    # エアコンID（最新）
    aircon_id = "e6680503-e88a-448b-aa4b-9bdb6d2640ab"  # 鎌ケ谷エアコン

    try:
        url = f"{BASE_URL}appliances/{aircon_id}/aircon_settings"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # 冷房26度でON
        data = "operation_mode=cool&temperature=26".encode()

        print(f"\n📤 送信情報:")
        print(f"   家電: エアコン1")
        print(f"   操作: 冷房26度ON")
        print(f"   URL: {url}")

        print(f"\n⚠️ 重要: Remoデバイスの赤外線LEDをよく見てください！")
        print(f"   送信開始まで3秒...")
        time.sleep(3)

        request = Request(url, data=data, headers=headers, method='POST')

        print(f"\n⏳ 送信中...")
        with urlopen(request) as response:
            result = loads(response.read().decode())

        print(f"\n✅ HTTPステータス: 200")
        print(f"\nレスポンス:")
        print(dumps(result, indent=2, ensure_ascii=False))

        print(f"\n" + "="*70)
        print(f"  ⚠️ 重要な確認")
        print(f"="*70)
        print(f"\n質問:")
        print(f"   1. Remoの赤外線LEDは点滅しましたか？")
        print(f"      - はい → Cloud APIは正常に信号を送信している")
        print(f"      - いいえ → Cloud APIは信号を送信していない")
        print(f"\n   2. エアコンは実際に動作しましたか？")
        print(f"      - はい → 信号送信成功、照明だけの問題")
        print(f"      - いいえ → API Key権限の問題")

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  🔧 エアコンLEDテスト")
    print("  目的: Cloud APIが実際に信号を送信しているか確認")
    print("="*70)

    test_aircon()

    print("\n" + "="*70)
    print("  📝 判定基準")
    print("="*70)

    print("\n【ケース1】Remoランプ点滅 + エアコン動作")
    print("   → Cloud API正常、照明のボタンが間違っている")
    print("   → '202'ボタンを見つける必要あり")

    print("\n【ケース2】Remoランプ点滅なし + エアコン動作せず")
    print("   → API KeyがRead-Only権限")
    print("   → API Keyの再発行が必要")

    print("\n【ケース3】Remoランプ点滅なし + エアコン動作した")
    print("   → ランプの見え方の問題（赤外線は出ている）")
    print("   → カメラで撮影すると見える可能性")

    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
