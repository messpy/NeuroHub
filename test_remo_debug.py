#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_remo_debug.py

Nature Remo デバッグ用テスト
APIレスポンスとデバイス状態を詳細確認
"""

import os
import sys
import time
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo API設定
REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def debug_api_call(method, endpoint, data=None):
    """API呼び出しのデバッグ情報を表示"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

    print(f"\n{'='*60}")
    print(f"API呼び出し: {method} {endpoint}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {REMO_API_KEY[:10]}...")

    if data:
        print(f"Data: {data}")

    try:
        if method == "GET":
            request = Request(url, headers=headers)
        elif method == "POST":
            if isinstance(data, str):
                data = data.encode()
            request = Request(url, data=data, headers=headers, method='POST')

        with urlopen(request) as response:
            response_data = response.read().decode()
            status_code = response.status

            print(f"\n✅ レスポンス:")
            print(f"Status: {status_code}")
            print(f"Body: {response_data[:200]}...")

            try:
                json_data = json.loads(response_data)
                return json_data
            except:
                return response_data

    except HTTPError as e:
        print(f"\n❌ HTTPエラー:")
        print(f"Status: {e.code}")
        print(f"Reason: {e.reason}")
        error_body = e.read().decode()
        print(f"Body: {error_body}")
        return None
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return None


def get_devices():
    """デバイス情報を取得"""
    print("\n" + "="*60)
    print("🔌 Remoデバイス情報")
    print("="*60)

    devices = debug_api_call("GET", "devices")

    if devices:
        for i, device in enumerate(devices, 1):
            print(f"\n{i}. {device.get('name')}")
            print(f"   ID: {device.get('id')}")
            print(f"   MAC: {device.get('mac_address')}")
            print(f"   ファームウェア: {device.get('firmware_version')}")
            print(f"   シリアル: {device.get('serial_number')}")

            # 最新イベント
            events = device.get('newest_events', {})
            if events:
                print(f"   最新イベント:")
                for event_type, event_data in events.items():
                    print(f"     {event_type}: {event_data}")

    return devices


def get_appliances():
    """家電一覧を取得"""
    print("\n" + "="*60)
    print("🏠 家電一覧")
    print("="*60)

    appliances = debug_api_call("GET", "appliances")

    if appliances:
        for i, appliance in enumerate(appliances, 1):
            print(f"\n{i}. {appliance.get('nickname')}")
            print(f"   ID: {appliance.get('id')}")
            print(f"   タイプ: {appliance.get('type')}")
            print(f"   モデル: {appliance.get('model')}")
            print(f"   デバイスID: {appliance.get('device', {}).get('id')}")

            # 照明の詳細情報
            if appliance.get('type') == 'LIGHT':
                light = appliance.get('light', {})
                print(f"   照明状態:")
                print(f"     state: {light.get('state', {})}")

                buttons = light.get('buttons', [])
                print(f"   ボタン ({len(buttons)}個):")
                for btn in buttons:
                    print(f"     - {btn.get('label')} (name: {btn.get('name')}, image: {btn.get('image', 'なし')[:20]}...)")

    return appliances


def test_light_control_with_debug(appliance_id, button_name):
    """照明制御のデバッグ"""
    print("\n" + "="*60)
    print(f"💡 照明制御テスト: {button_name}")
    print("="*60)

    endpoint = f"appliances/{appliance_id}/light"
    data = f"button={button_name}"

    result = debug_api_call("POST", endpoint, data)

    return result


def check_signal_send():
    """信号送信履歴を確認（可能であれば）"""
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
