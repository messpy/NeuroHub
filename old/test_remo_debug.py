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


def test_off_button_detailed():
    """OFFボタン詳細テスト"""
    print("\n" + "="*70)
    print("  🔍 OFFボタン詳細テスト")
    print("  問題: Remoランプが全く点滅しない")
    print("="*70)

    appliance_id = "afca7f43-d75b-4be1-aa5c-fc608b5acc4b"

    # 方法1: application/x-www-form-urlencoded
    print("\n📤 方法1: application/x-www-form-urlencoded")
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = "button=off".encode()

        print(f"   URL: {url}")
        print(f"   Headers:")
        print(f"      Authorization: Bearer {REMO_API_KEY[:10]}...")
        print(f"      Content-Type: application/x-www-form-urlencoded")
        print(f"   Body: button=off")

        request = Request(url, data=data, headers=headers, method='POST')

        print(f"\n   ⏳ 送信中...")
        with urlopen(request) as response:
            result = loads(response.read().decode())

        print(f"   ✅ HTTPステータス: 200")
        print(f"   レスポンス:")
        print(f"      {dumps(result, indent=6, ensure_ascii=False)}")

        print(f"\n   ⚠️ 重要: Remoランプは点滅しましたか？")
        response_user = input("   点滅した場合は 'y' を入力: ")

        if response_user.lower() == 'y':
            print(f"   ✅ 方法1で信号送信確認！")
            return True
        else:
            print(f"   ❌ 方法1では信号送信されていない")

    except Exception as e:
        print(f"   ❌ エラー: {e}")

    return False


def check_devices():
    """Remoデバイス一覧を確認"""
    print("\n" + "="*70)
    print("  � Remoデバイス確認")
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

            # ネットワーク情報
            newest_events = device.get('newest_events', {})
            if newest_events:
                print(f"  最新イベント:")
                for event_type, event in newest_events.items():
                    print(f"    {event_type}: {event.get('created_at')}")

            # 温度センサー
            if 'te' in newest_events:
                print(f"  温度: {newest_events['te'].get('val')}°C")

            # 湿度センサー
            if 'hu' in newest_events:
                print(f"  湿度: {newest_events['hu'].get('val')}%")

    except Exception as e:
        print(f"❌ エラー: {e}")


def check_all_ir_appliances():
    """全IR家電を確認して'202'を探す"""
    print("\n" + "="*70)
    print("  🔍 全IR家電確認（'202'を探す）")
    print("="*70)

    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = loads(response.read().decode())

        print(f"\n✅ 家電数: {len(appliances)}")

        # IR家電だけをフィルタ
        ir_appliances = [app for app in appliances if app.get('type') == 'IR']

        print(f"✅ IR家電数: {len(ir_appliances)}")

        # '202'を含む信号を探す
        found_202 = False

        for i, app in enumerate(ir_appliances, 1):
            nickname = app.get('nickname', '')
            signals = app.get('signals', [])

            print(f"\nIR家電 {i}: {nickname}")
            print(f"  信号数: {len(signals)}")

            for signal in signals:
                signal_name = signal.get('name', '')
                signal_id = signal.get('id', '')

                if '202' in signal_name.lower() or '202' in signal_id.lower():
                    found_202 = True
                    print(f"  🎯 '202'信号発見！")
                    print(f"     信号ID: {signal_id}")
                    print(f"     信号名: {signal_name}")
                    print(f"     イメージ: {signal.get('image', 'なし')}")

        if not found_202:
            print(f"\n⚠️ IR家電に'202'という信号は見つかりませんでした")

    except Exception as e:
        print(f"❌ エラー: {e}")


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  � Nature Remo OFFボタンデバッグ")
    print("  問題: Remoランプが全く点滅しない")
    print("="*70)

    # 1. デバイス確認
    check_devices()

    # 2. OFFボタンテスト
    signal_sent = test_off_button_detailed()

    # 3. IR家電の'202'信号確認
    check_all_ir_appliances()

    print("\n" + "="*70)
    print("  📝 調査結果まとめ")
    print("="*70)

    if not signal_sent:
        print("\n❌ 重要な問題:")
        print("   Remoランプが点滅していない = 赤外線信号が送信されていない")
        print("\n🔍 考えられる原因:")
        print("   1. API KeyがRead-Onlyになっている")
        print("   2. TAKIZUMIが別のデバイスに紐付いている")
        print("   3. Cloud APIが実際には信号を送信していない")
        print("   4. ネットワーク遅延で信号が届いていない")

    print("\n💡 次のステップ:")
    print("   1. Remoアプリで'202'の場所を確認")
    print("   2. ローカルAPI経由での送信テスト")
    print("   3. API Keyの権限確認")

    print("\n✅ デバッグ完了")


if __name__ == "__main__":
    main()

    print("\n" + "="*60)
    print("📡 信号送信履歴")
    print("="*60)

    # Remo 1以降では信号送信履歴は取得できないが、試してみる
    signals = debug_api_call("GET", "1/signals")

    if signals:
        print(f"✅ 信号履歴取得成功: {len(signals)}件")
    else:
        print("⚠️ 信号履歴は取得できません（Remo 1以降では非対応）")


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  🔍 Nature Remo デバッグテスト")
    print("="*60)

    if not REMO_API_KEY:
        print("❌ REMO_API環境変数が設定されていません")
        return

    # 1. デバイス情報確認
    devices = get_devices()

    # 2. 家電一覧確認
    appliances = get_appliances()

    # 3. TAKIZUMI検索
    light = None
    for appliance in appliances:
        if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == 'TAKIZUMI':
            light = appliance
            break

    if not light:
        print("\n❌ TAKIZUMI が見つかりません")
        return

    appliance_id = light.get('id')
    print(f"\n✅ TAKIZUMI検出: ID={appliance_id}")

    # 4. 照明制御テスト
    print("\n" + "="*60)
    print("  照明制御実行")
    print("="*60)

    # ONテスト
    print("\n1️⃣ 照明ON実行中...")
    result_on = test_light_control_with_debug(appliance_id, "on")

    if result_on is not None:
        print("✅ ON信号送信成功")
    else:
        print("❌ ON信号送信失敗")

    # 5秒待機
    print("\n⏳ 5秒待機...")
    time.sleep(5)

    # OFFテスト
    print("\n2️⃣ 照明OFF実行中...")
    result_off = test_light_control_with_debug(appliance_id, "off")

    if result_off is not None:
        print("✅ OFF信号送信成功")
    else:
        print("❌ OFF信号送信失敗")

    # 5. 最終確認
    print("\n" + "="*60)
    print("  最終確認")
    print("="*60)

    print("\n📊 実行結果:")
    print(f"   デバイス数: {len(devices) if devices else 0}")
    print(f"   家電数: {len(appliances) if appliances else 0}")
    print(f"   TAKIZUMI ID: {appliance_id}")
    print(f"   ON信号: {'✅ 成功' if result_on is not None else '❌ 失敗'}")
    print(f"   OFF信号: {'✅ 成功' if result_off is not None else '❌ 失敗'}")

    print("\n💡 確認事項:")
    print("   1. 実際に照明がON/OFFされましたか？")
    print("   2. Remoデバイスのランプが点滅しましたか？")
    print("   3. 照明がRemoアプリで正しく登録されていますか？")
    print("   4. Remoと照明の間に障害物はありませんか？")

    print("\n✅ デバッグテスト完了")


if __name__ == "__main__":
    main()
