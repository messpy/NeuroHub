#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_aircon.py

Nature Remo エアコン制御テスト
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


def get_appliances():
    """家電一覧を取得"""
    try:
        url = f"{BASE_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            data = json.loads(response.read().decode())

        return data
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def find_aircon(appliances, nickname=None):
    """エアコンを検索"""
    aircons = []
    for appliance in appliances:
        if appliance.get('type') == 'AC':
            aircons.append(appliance)

    if not aircons:
        return None

    if nickname:
        for ac in aircons:
            if ac.get('nickname') == nickname:
                return ac

    # ニックネームが指定されていない場合は最初のエアコン
    return aircons[0]


def show_aircon_settings(aircon):
    """エアコンの設定を表示"""
    print(f"\n📊 現在の設定:")
    settings = aircon.get('settings', {})

    print(f"   温度: {settings.get('temp', 'N/A')}°C")
    print(f"   モード: {settings.get('mode', 'N/A')}")
    print(f"   風量: {settings.get('vol', 'N/A')}")
    print(f"   風向: {settings.get('dir', 'N/A')}")
    print(f"   ボタン: {settings.get('button', 'N/A')}")

    return settings


def control_aircon(appliance_id, settings):
    """エアコンを制御"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/aircon_settings"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        # POSTデータを作成
        params = []
        if 'temperature' in settings:
            params.append(f"temperature={settings['temperature']}")
        if 'operation_mode' in settings:
            params.append(f"operation_mode={settings['operation_mode']}")
        if 'air_volume' in settings:
            params.append(f"air_volume={settings['air_volume']}")
        if 'air_direction' in settings:
            params.append(f"air_direction={settings['air_direction']}")
        if 'button' in settings:
            params.append(f"button={settings['button']}")

        data = "&".join(params).encode()

        print(f"\n📤 送信データ: {data.decode()}")

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())

        print(f"✅ 制御成功")
        return result

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        error_body = e.read().decode()
        print(f"   詳細: {error_body}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def turn_on_aircon(appliance_id):
    """エアコンをONにする（冷房26度）"""
    settings = {
        'operation_mode': 'cool',  # 冷房
        'temperature': '26'        # 26度
    }
    return control_aircon(appliance_id, settings)


def turn_off_aircon(appliance_id):
    """エアコンをOFFにする"""
    settings = {
        'button': 'power-off'
    }
    return control_aircon(appliance_id, settings)


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  ❄️ Nature Remo エアコン制御テスト")
    print("="*60)

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

    # エアコン一覧表示
    aircons = [a for a in appliances if a.get('type') == 'AC']

    if not aircons:
        print("❌ エアコンが見つかりません")
        return

    print(f"\n✅ {len(aircons)}台のエアコンを検出:")
    for i, ac in enumerate(aircons, 1):
        print(f"\n{i}. {ac.get('nickname')}")
        print(f"   ID: {ac.get('id')}")
        show_aircon_settings(ac)

    # 最初のエアコンを使用
    aircon = aircons[0]
    appliance_id = aircon.get('id')

    print(f"\n🎯 テスト対象: {aircon.get('nickname')}")

    # エアコン制御テスト
    print("\n" + "="*60)
    print("  エアコン制御実行")
    print("="*60)

    # ONテスト
    print("\n1️⃣ エアコンをONにします（冷房26度）...")
    result_on = turn_on_aircon(appliance_id)

    if result_on:
        print(f"\n✅ ON信号送信成功")
        print(f"   温度: {result_on.get('temp')}°C")
        print(f"   モード: {result_on.get('mode')}")
        print(f"   風量: {result_on.get('vol')}")
        print(f"\n💡 エアコンが起動しましたか？")
    else:
        print("❌ ON信号送信失敗")

    # 5秒待機
    print("\n⏳ 5秒待機...")
    time.sleep(5)

    # OFFテスト
    print("\n2️⃣ エアコンをOFFにします...")
    result_off = turn_off_aircon(appliance_id)

    if result_off:
        print(f"\n✅ OFF信号送信成功")
        print(f"\n💡 エアコンが停止しましたか？")
    else:
        print("❌ OFF信号送信失敗")

    print("\n" + "="*60)
    print("  ✅ テスト完了")
    print("="*60)

    print("\n📊 実行結果:")
    print(f"   エアコン数: {len(aircons)}")
    print(f"   テスト対象: {aircon.get('nickname')}")
    print(f"   ON信号: {'✅ 成功' if result_on else '❌ 失敗'}")
    print(f"   OFF信号: {'✅ 成功' if result_off else '❌ 失敗'}")

    print("\n💡 確認事項:")
    print("   1. 実際にエアコンがON/OFFされましたか？")
    print("   2. Remoデバイスのランプが点滅しましたか？")


if __name__ == "__main__":
    main()
