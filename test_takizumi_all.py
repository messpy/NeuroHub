#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_takizumi_all.py

TAKIZUMI照明の全ボタンテスト
全6ボタンを順番に実行して、実際の反応を確認
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


def get_takizumi():
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


def send_button(appliance_id, button_name, button_label):
    """ボタン信号を送信"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        data = f"button={button_name}".encode()

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = loads(response.read().decode())

        return result

    except HTTPError as e:
        if e.code == 429:
            print(f"   ⚠️ レート制限: しばらく待機してください")
        else:
            print(f"   ❌ HTTPエラー: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return None


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  💡 TAKIZUMI 全ボタンテスト")
    print("  全6ボタンを順番に実行します")
    print("="*70)

    if not REMO_API_KEY:
        print("❌ REMO_API環境変数が設定されていません")
        return

    print(f"\n✅ API Key確認: {REMO_API_KEY[:10]}...")

    # TAKIZUMI取得
    print("\n🔍 TAKIZUMI検索中...")
    light = get_takizumi()

    if not light:
        print("❌ TAKIZUMI が見つかりません")
        return

    appliance_id = light.get('id')
    print(f"✅ 照明検出: {light.get('nickname')}")
    print(f"   ID: {appliance_id}")

    # ボタン一覧
    light_data = light.get('light', {})
    buttons = light_data.get('buttons', [])
    current_state = light_data.get('state', {})

    print(f"\n📊 現在の状態:")
    print(f"   power: {current_state.get('power')}")
    print(f"   brightness: {current_state.get('brightness')}")
    print(f"   last_button: {current_state.get('last_button')}")

    print(f"\n🎯 利用可能なボタン: {len(buttons)}個")
    for i, btn in enumerate(buttons, 1):
        print(f"  {i}. {btn.get('label'):10s} (name: {btn.get('name')})")

    print("\n" + "="*70)
    print("  📡 全ボタン実行開始")
    print("  各ボタン実行後、照明の反応を確認してください")
    print("="*70)

    print("\n⚠️ 重要:")
    print("  - 各ボタン実行後、10秒待機します（レート制限回避）")
    print("  - 照明が反応したボタンをメモしてください")
    print("  - Remoデバイスのランプ点滅も確認してください\n")

    input("準備ができたらEnterキーを押してください...")

    # 全ボタンを順番に実行
    results = []

    for i, btn in enumerate(buttons, 1):
        label = btn.get('label')
        name = btn.get('name')

        print(f"\n{'='*70}")
        print(f"  ボタン {i}/{len(buttons)}: {label} (name: {name})")
        print(f"{'='*70}")

        # 10秒待機（レート制限回避）
        if i > 1:
            print(f"\n⏳ 10秒待機中（レート制限回避）...")
            for remaining in range(10, 0, -1):
                print(f"   残り {remaining}秒...", end='\r')
                time.sleep(1)
            print()  # 改行

        print(f"\n📤 信号送信中...")
        result = send_button(appliance_id, name, label)

        if result:
            power = result.get('power')
            brightness = result.get('brightness')
            last_button = result.get('last_button')

            print(f"✅ API成功:")
            print(f"   power: {power}")
            print(f"   brightness: {brightness}")
            print(f"   last_button: {last_button}")

            results.append({
                'button': label,
                'name': name,
                'api_success': True,
                'power': power,
                'brightness': brightness
            })

            print(f"\n💡 照明の反応を確認してください:")
            print(f"   - 点灯した？")
            print(f"   - 消灯した？")
            print(f"   - 明るさが変わった？")
            print(f"   - 何も変化しなかった？")
            print(f"   - Remoのランプは点滅した？")

            # 5秒観察時間
            print(f"\n⏳ 5秒観察中...")
            time.sleep(5)
        else:
            results.append({
                'button': label,
                'name': name,
                'api_success': False
            })

    # 結果まとめ
    print("\n" + "="*70)
    print("  📊 テスト結果まとめ")
    print("="*70)

    print("\n全ボタンのAPI実行結果:")
    for i, result in enumerate(results, 1):
        button = result['button']
        name = result['name']
        api_status = "✅ 成功" if result['api_success'] else "❌ 失敗"

        if result['api_success']:
            power = result.get('power', 'N/A')
            brightness = result.get('brightness', 'N/A')
            print(f"  {i}. {button:10s} (name: {name:12s}) - {api_status}")
            print(f"      → power: {power}, brightness: {brightness}")
        else:
            print(f"  {i}. {button:10s} (name: {name:12s}) - {api_status}")

    print("\n" + "="*70)
    print("  🔍 確認事項")
    print("="*70)

    print("\n1. どのボタンで照明が実際に反応しましたか？")
    print("   例: ON, OFF, All, Night, Bright, Dark")
    print("   または: どれも反応しなかった")

    print("\n2. Remoデバイスのランプは点滅しましたか？")
    print("   - 点滅した → Remoは信号を送信している")
    print("   - 点滅しない → Remoに信号が届いていない")

    print("\n3. 反応したボタンの特徴はありますか？")
    print("   - 特定のボタンだけ反応する")
    print("   - 全て反応する")
    print("   - 全て反応しない")

    print("\n4. Remoアプリから操作すると照明は動きますか？")
    print("   - 動く → API実装に違いがある")
    print("   - 動かない → Remoまたは照明の設定問題")

    print("\n5. 照明とRemoの位置関係:")
    print("   - 距離: 3m以内推奨")
    print("   - 障害物: なし推奨")
    print("   - 照明の受信部がRemoに向いているか")

    print("\n✅ テスト完了")
    print("\n結果を教えてください！")


if __name__ == "__main__":
    main()
