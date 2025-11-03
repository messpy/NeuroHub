#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_remo_debug.py

Remo信号送信デバッグ
ランプが点滅しない原因を調査 - OFFボタン集中テスト
"""

import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from json import loads, dumps
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo API設定
REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def test_off_button():
    """OFFボタンテスト"""
    print("\n" + "="*70)
    print("  🔍 OFFボタンテスト")
    print("="*70)

    appliance_id = "afca7f43-d75b-4be1-aa5c-fc608b5acc4b"

    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = "button=off".encode()

        print(f"\n📤 送信情報:")
        print(f"   URL: {url}")
        print(f"   Authorization: Bearer {REMO_API_KEY[:10]}...")
        print(f"   Content-Type: application/x-www-form-urlencoded")
        print(f"   Body: button=off")

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
        print(f"\n1. Remoデバイスの赤外線LEDは点滅しましたか？")
        print(f"   - 点滅した → API正常動作、照明側の問題")
        print(f"   - 点滅しなかった → APIが信号を送信していない")

        return True

    except HTTPError as e:
        print(f"\n❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   Body: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


def check_ir_signals():
    """IR家電の信号を確認して'202'を探す"""
    print("\n" + "="*70)
    print("  🔍 IR家電の信号確認（'202'を探す）")
    print("="*70)

    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = loads(response.read().decode())

        # IR家電だけをフィルタ
        ir_appliances = [app for app in appliances if app.get('type') == 'IR']

        print(f"\n✅ IR家電数: {len(ir_appliances)}")

        found_202 = False

        for i, app in enumerate(ir_appliances, 1):
            nickname = app.get('nickname', '')
            signals = app.get('signals', [])

            print(f"\nIR家電 {i}: {nickname}")
            print(f"  信号数: {len(signals)}")

            # 全信号をチェック
            for signal in signals:
                signal_name = signal.get('name', '')
                signal_id = signal.get('id', '')

                # '202'を探す
                if '202' in signal_name or '202' in signal_id:
                    found_202 = True
                    print(f"\n  🎯 '202'発見！")
                    print(f"     家電: {nickname}")
                    print(f"     信号ID: {signal_id}")
                    print(f"     信号名: {signal_name}")
                    print(f"     イメージ: {signal.get('image', 'なし')}")

                # 先頭3個だけ表示（全部は多すぎる）
                if signals.index(signal) < 3:
                    print(f"     信号{signals.index(signal)+1}: {signal_name}")

            if len(signals) > 3:
                print(f"     ... 他 {len(signals)-3} 個の信号")

        if not found_202:
            print(f"\n⚠️ '202'という信号は見つかりませんでした")

        return found_202

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


def check_devices():
    """Remoデバイス状態を確認"""
    print("\n" + "="*70)
    print("  🔍 Remoデバイス状態")
    print("="*70)

    try:
        url = f"{BASE_URL}devices"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            devices = loads(response.read().decode())

        print(f"\n✅ デバイス数: {len(devices)}")

        for i, device in enumerate(devices, 1):
            print(f"\nデバイス {i}:")
            print(f"  名前: {device.get('name')}")
            print(f"  ID: {device.get('id')}")
            print(f"  MAC: {device.get('mac_address')}")
            print(f"  ファームウェア: {device.get('firmware_version')}")

            # 最新イベント（最後に通信した時刻）
            newest_events = device.get('newest_events', {})
            if 'te' in newest_events:
                created_at = newest_events['te'].get('created_at')
                print(f"  最終通信: {created_at}")
                print(f"  温度: {newest_events['te'].get('val')}°C")

            if 'hu' in newest_events:
                print(f"  湿度: {newest_events['hu'].get('val')}%")

    except Exception as e:
        print(f"\n❌ エラー: {e}")


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  🔧 Nature Remo デバッグツール")
    print("  問題: Remoランプが全く点滅しない → 信号が送信されていない")
    print("="*70)

    print(f"\n✅ API Key確認: {REMO_API_KEY[:10]}...")

    # 1. デバイス状態確認
    check_devices()

    # 2. OFFボタンテスト
    test_off_button()

    # 3. IR家電の'202'信号確認
    found_202 = check_ir_signals()

    # 結果まとめ
    print("\n" + "="*70)
    print("  📝 調査結果まとめ")
    print("="*70)

    print("\n🔍 判明した事実:")
    print("   1. Cloud APIはHTTPステータス200を返す（API呼び出し成功）")
    print("   2. レスポンスに照明状態が含まれる（power, brightness更新）")
    print("   3. Remoランプが点滅しない → 実際には信号を送信していない")

    if found_202:
        print(f"\n✅ '202'信号を発見しました！")
        print(f"   Remoアプリの'202'はこの信号かもしれません")
    else:
        print(f"\n⚠️ '202'信号は見つかりませんでした")

    print("\n💡 考えられる原因:")
    print("   1. API KeyがRead-Only権限（信号送信不可）")
    print("   2. Cloud APIは状態更新のみで実際の信号送信は別処理")
    print("   3. TAKIZUMIが別のデバイスに紐付いている")
    print("   4. ネットワーク設定の問題")

    print("\n🔧 次のステップ:")
    print("   1. Remoアプリで'202'の詳細確認（スクリーンショット）")
    print("   2. API Keyの権限確認（Read/Write）")
    print("   3. ローカルAPI経由での送信テスト")
    print("   4. 別の家電（エアコン、テレビ）でランプ点滅確認")

    print("\n✅ デバッグ完了")


if __name__ == "__main__":
    main()
