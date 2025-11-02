#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_light_control.py

Nature Remo 照明制御テスト（簡易版）
入力なしで自動的にON/OFF切り替え
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


def get_appliances():
    """家電一覧取得"""
    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            data = loads(response.read().decode())

        return data
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def find_light(appliances, nickname="TAKIZUMI"):
    """照明を検索"""
    for appliance in appliances:
        if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == nickname:
            return appliance
    return None


def control_light(appliance, button_name):
    """照明制御"""
    try:
        device_id = appliance.get('id')
        url = f"{BASE_URL}appliances/{device_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        # POSTデータ
        data = f"button={button_name}".encode()

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = response.read().decode()

        return True
    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("  💡 Nature Remo 照明制御テスト")
    print("=" * 60)

    if not REMO_API_KEY:
        print("❌ REMO_API環境変数が設定されていません")
        return

    print(f"\n✅ API Key確認: {REMO_API_KEY[:10]}...")

    # 家電一覧取得
    print("\n📋 家電一覧取得中...")
    appliances = get_appliances()

    if not appliances:
        print("❌ 家電一覧の取得に失敗しました")
        return

    print(f"✅ {len(appliances)}個の家電を取得")

    # 照明検索
    print("\n🔍 TAKIZUMI を検索中...")
    light = find_light(appliances, "TAKIZUMI")

    if not light:
        print("❌ TAKIZUMI が見つかりません")
        return

    print(f"✅ 照明検出: {light.get('nickname')}")

    # ボタン一覧
    light_data = light.get('light', {})
    buttons = light_data.get('buttons', [])

    print(f"\n🎯 利用可能なボタン ({len(buttons)}個):")
    for btn in buttons:
        print(f"   - {btn.get('label')} (name: {btn.get('name')})")

    # ON/OFFテスト
    print("\n" + "=" * 60)
    print("  🔆 照明制御テスト開始")
    print("=" * 60)

    # ONテスト
    print("\n1️⃣ 照明をONにします...")
    if control_light(light, "on"):
        print("✅ 💡 照明をONにしました")
    else:
        print("❌ 制御に失敗しました")
        return

    # 3秒待機
    print("\n⏳ 3秒待機...")
    time.sleep(3)

    # OFFテスト
    print("\n2️⃣ 照明をOFFにします...")
    if control_light(light, "off"):
        print("✅ 🌙 照明をOFFにしました")
    else:
        print("❌ 制御に失敗しました")
        return

    print("\n" + "=" * 60)
    print("  ✅ テスト完了")
    print("=" * 60)

    print("\n📊 実行結果:")
    print("   ✅ 照明ON成功")
    print("   ✅ 照明OFF成功")
    print("\n💡 実際に照明がON/OFFされたか確認してください！")


if __name__ == "__main__":
    main()
