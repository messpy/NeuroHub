#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_light_advanced.py

Nature Remo 照明制御テスト（詳細版）
異なるヘッダーやデータフォーマットを試す
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


def get_light():
    """TAKIZUMI照明を取得"""
    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = json.loads(response.read().decode())

        for appliance in appliances:
            if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == 'TAKIZUMI':
                return appliance

        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def test_light_method_1(appliance_id, button):
    """方法1: application/x-www-form-urlencoded（標準）"""
    print(f"\n{'='*60}")
    print("方法1: application/x-www-form-urlencoded")
    print(f"{'='*60}")

    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = f"button={button}".encode()

        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data.decode()}")

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())

        print(f"✅ 成功: {result}")
        return True
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False


def test_light_method_2(appliance_id, button):
    """方法2: JSON形式"""
    print(f"\n{'='*60}")
    print("方法2: application/json")
    print(f"{'='*60}")

    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}",
            "Content-Type": "application/json"
        }

        data = json.dumps({"button": button}).encode()

        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data.decode()}")

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())

        print(f"✅ 成功: {result}")
        return True
    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False


def test_light_method_3(appliance_id, button):
    """方法3: ヘッダーなし（最小限）"""
    print(f"\n{'='*60}")
    print("方法3: ヘッダーなし（最小限）")
    print(f"{'='*60}")

    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}"
        }

        data = f"button={button}".encode()

        print(f"URL: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data.decode()}")

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())

        print(f"✅ 成功: {result}")
        return True
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False


def test_light_method_4(appliance_id, button):
    """方法4: クエリパラメータ"""
    print(f"\n{'='*60}")
    print("方法4: クエリパラメータ")
    print(f"{'='*60}")

    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light?button={button}"
        headers = {
            "Authorization": f"Bearer {REMO_API_KEY}"
        }

        print(f"URL: {url}")
        print(f"Headers: {headers}")

        request = Request(url, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())

        print(f"✅ 成功: {result}")
        return True
    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False


def test_signal_via_api(appliance_id):
    """方法5: 信号IDを使って送信"""
    print(f"\n{'='*60}")
    print("方法5: 信号ID経由での送信")
    print(f"{'='*60}")

    try:
        # まず家電情報を取得してボタンのimage（信号ID）を取得
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = json.loads(response.read().decode())

        # TAKIZUMIを検索
        light = None
        for appliance in appliances:
            if appliance.get('id') == appliance_id:
                light = appliance
                break

        if not light:
            print("❌ 照明が見つかりません")
            return False

        # ONボタンの信号IDを取得
        buttons = light.get('light', {}).get('buttons', [])
        on_signal_id = None

        for btn in buttons:
            if btn.get('name') == 'on':
                on_signal_id = btn.get('image')
                break

        if not on_signal_id:
            print("❌ ON信号IDが見つかりません")
            return False

        print(f"ON信号ID: {on_signal_id}")

        # 信号を送信
        url = f"{BASE_URL}signals/{on_signal_id}/send"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        print(f"URL: {url}")

        request = Request(url, headers=headers, method='POST')
        with urlopen(request) as response:
            result = response.read().decode()

        print(f"✅ 成功: {result}")
        return True

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  💡 Nature Remo 照明制御テスト（詳細版）")
    print("  異なる方法を試して動作を確認")
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
    print(f"   ID: {appliance_id}")

    # ボタン情報表示
    buttons = light.get('light', {}).get('buttons', [])
    print(f"\n🎯 利用可能なボタン:")
    for btn in buttons:
        print(f"   - {btn.get('label')} (name: {btn.get('name')})")

    print("\n" + "="*60)
    print("  テスト開始: ONボタンを各方法で送信")
    print("="*60)

    # 各方法を試す
    methods = [
        ("方法1", lambda: test_light_method_1(appliance_id, "on")),
        ("方法2", lambda: test_light_method_2(appliance_id, "on")),
        ("方法3", lambda: test_light_method_3(appliance_id, "on")),
        ("方法4", lambda: test_light_method_4(appliance_id, "on")),
        ("方法5", lambda: test_signal_via_api(appliance_id)),
    ]

    results = {}

    for method_name, method_func in methods:
        print(f"\n{'='*60}")
        print(f"  {method_name} 実行中...")
        print(f"{'='*60}")

        success = method_func()
        results[method_name] = success

        if success:
            print(f"\n💡 照明が反応しましたか？（3秒観察）")
            time.sleep(3)

    # 結果まとめ
    print("\n" + "="*60)
    print("  📊 テスト結果まとめ")
    print("="*60)

    for method_name, success in results.items():
        status = "✅ API成功" if success else "❌ API失敗"
        print(f"{method_name}: {status}")

    print("\n💡 どの方法で照明が反応しましたか？")
    print("   成功した方法を教えてください！")


if __name__ == "__main__":
    main()
