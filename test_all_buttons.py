#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_all_buttons.py

Nature Remo 全ボタン実行テスト
TAKIZUMIの全ボタンを順番に実行して、どれが実際に動作するか確認
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


def send_button(appliance_id, button_name, button_label):
    """ボタン信号を送信"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        data = f"button={button_name}".encode()

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = loads(response.read().decode())

        print(f"   ✅ API成功: power={result.get('power')}, brightness={result.get('brightness')}, last_button={result.get('last_button')}")
        return True

    except HTTPError as e:
        print(f"   ❌ HTTPエラー: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  💡 Nature Remo 全ボタンテスト")
    print("  各ボタンを順番に実行して、照明が反応するか確認します")
    print("="*70)

    if not REMO_API_KEY:
        print("❌ REMO_API環境変数が設定されていません")
        return

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

    # ボタン一覧
    light_data = light.get('light', {})
    buttons = light_data.get('buttons', [])

    print(f"\n🎯 利用可能なボタン: {len(buttons)}個")
    for i, btn in enumerate(buttons, 1):
        print(f"  {i}. {btn.get('label'):10s} (name: {btn.get('name')})")

    print("\n" + "="*70)
    print("  📡 全ボタン実行開始")
    print("="*70)
    print("\n⚠️ 各ボタン実行後、照明が反応するか目視で確認してください！")
    print("   反応したボタンをメモしておいてください。\n")

    input("Enterキーを押して開始...")

    # 全ボタンを順番に実行
    results = {}

    for i, btn in enumerate(buttons, 1):
        label = btn.get('label')
        name = btn.get('name')

        print(f"\n{'='*70}")
        print(f"  ボタン {i}/{len(buttons)}: {label} (name: {name})")
        print(f"{'='*70}")

        print(f"\n📤 信号送信中...")
        success = send_button(appliance_id, name, label)

        results[name] = {
            'label': label,
            'api_success': success
        }

        if success:
            print(f"\n💡 照明は反応しましたか？")
            print(f"   - YES: 点灯/消灯/明るさが変化した")
            print(f"   - NO:  何も変化しなかった")
            print(f"\n⏳ 5秒観察中... (次のボタンまで待機)")

        # 次のボタンまで5秒待機
        time.sleep(5)

    # 結果まとめ
    print("\n" + "="*70)
    print("  📊 テスト結果まとめ")
    print("="*70)

    print("\n全ボタンのAPI実行結果:")
    for i, btn in enumerate(buttons, 1):
        name = btn.get('name')
        result = results.get(name, {})
        label = result.get('label', name)
        api_status = "✅ 成功" if result.get('api_success') else "❌ 失敗"

        print(f"  {i}. {label:10s} (name: {name:12s}) - API: {api_status}")

    print("\n" + "="*70)
    print("  重要な質問:")
    print("="*70)
    print("\n1. どのボタンで照明が実際に反応しましたか？")
    print("   例: ON, OFF, All, Night, Bright, Dark, どれも反応しなかった")
    print("\n2. Remoデバイス本体のランプは点滅しましたか？")
    print("   - 点滅した → Remoは信号を送信している")
    print("   - 点滅しない → Remoがネットワークから信号を受信していない")
    print("\n3. Remoと照明の距離はどのくらいですか？")
    print("   - 推奨: 3m以内、障害物なし")
    print("\n4. Remoアプリから操作すると照明は動きますか？")
    print("   - 動く → API実装に違いがある可能性")
    print("   - 動かない → Remoまたは照明の設定問題")

    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
