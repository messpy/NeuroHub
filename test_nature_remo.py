#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_nature_remo.py

Nature Remo API 動作テスト
"""

import os
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from json import loads
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo API設定
REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def test_api_connection():
    """API接続テスト"""
    print("=" * 50)
    print("Nature Remo API 接続テスト")
    print("=" * 50)

    if not REMO_API_KEY:
        print("❌ REMO_API環境変数が設定されていません")
        return False

    print(f"✅ API Key: {REMO_API_KEY[:10]}...")
    return True


def get_appliances():
    """家電一覧取得"""
    print("\n📋 家電一覧取得中...")

    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            data = loads(response.read().decode())

        print(f"✅ 取得成功: {len(data)}個の家電")

        for i, appliance in enumerate(data, 1):
            print(f"\n{i}. {appliance.get('nickname', '名前なし')}")
            print(f"   タイプ: {appliance.get('type', '不明')}")
            print(f"   ID: {appliance.get('id', 'なし')}")

            # デバイス情報
            device = appliance.get('device', {})
            print(f"   デバイス名: {device.get('name', '不明')}")

            # 照明の場合はボタン一覧表示
            if appliance.get('type') == 'LIGHT':
                light = appliance.get('light', {})
                buttons = light.get('buttons', [])
                print(f"   ボタン数: {len(buttons)}")
                for btn in buttons:
                    print(f"     - {btn.get('label', '不明')} ({btn.get('name', 'なし')})")

        return data

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def find_light(appliances, nickname="TAKIZUMI"):
    """照明を検索"""
    print(f"\n🔍 照明 '{nickname}' を検索中...")

    for appliance in appliances:
        if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == nickname:
            print(f"✅ 見つかりました: {appliance.get('nickname')}")
            return appliance

    print(f"❌ 照明 '{nickname}' が見つかりません")
    return None


def control_light(appliance, button_name):
    """照明制御"""
    print(f"\n🎛️ 照明制御: {button_name}")

    try:
        device_id = appliance.get('id')
        url = f"{BASE_URL}appliances/{device_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        # POSTデータ
        data = f"button={button_name}".encode()

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = response.read().decode()

        print(f"✅ 制御成功: {button_name}")
        return True

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("\n🏠 Nature Remo API テストスクリプト\n")

    # API接続確認
    if not test_api_connection():
        return

    # 家電一覧取得
    appliances = get_appliances()
    if not appliances:
        print("\n❌ 家電一覧の取得に失敗しました")
        return

    # 照明検索
    light = find_light(appliances, "TAKIZUMI")
    if not light:
        print("\n💡 利用可能な照明:")
        for appliance in appliances:
            if appliance.get('type') == 'LIGHT':
                print(f"  - {appliance.get('nickname')}")
        return

    # ボタン一覧表示
    print("\n🎯 利用可能なボタン:")
    light_data = light.get('light', {})
    buttons = light_data.get('buttons', [])

    for i, btn in enumerate(buttons, 1):
        label = btn.get('label', '不明')
        name = btn.get('name', 'なし')
        print(f"  {i}. {label} (name: {name})")

    # ON/OFFボタン検出
    on_button = None
    off_button = None

    for btn in buttons:
        label_lower = btn.get('label', '').lower()
        if "on" in label_lower or "オン" in label_lower or "点灯" in label_lower:
            on_button = btn.get('name')
        elif "off" in label_lower or "オフ" in label_lower or "消灯" in label_lower:
            off_button = btn.get('name')

    print(f"\n🔍 自動検出結果:")
    print(f"  ONボタン: {on_button}")
    print(f"  OFFボタン: {off_button}")

    # テスト実行確認
    print("\n" + "=" * 50)
    response = input("照明制御テストを実行しますか？ (y/N): ")

    if response.lower() == 'y':
        if on_button:
            print("\n--- ON テスト ---")
            control_light(light, on_button)
            input("Enter キーを押して続行...")

            print("\n--- OFF テスト ---")
            if off_button:
                control_light(light, off_button)
            else:
                print("⚠️ OFFボタンが検出されませんでした")
        else:
            print("⚠️ ONボタンが検出されませんでした")
    else:
        print("テストをスキップしました")

    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
