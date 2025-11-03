#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_takizumi_buttons.py

TAKIZUMI照明の全ボタンを詳細調査
隠れたボタンや実際に使えるボタンを発見
"""

import os
import sys
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo API設定
REMO_API_KEY = os.getenv('REMO_API')
BASE_URL = "https://api.nature.global/1/"


def get_appliance_detail(appliance_id):
    """家電の詳細情報を取得"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            data = json.loads(response.read().decode())

        return data
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


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


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  🔍 TAKIZUMI照明 詳細調査")
    print("="*70)

    # 家電一覧取得
    print("\n📋 家電一覧取得中...")
    appliances = get_appliances()

    if not appliances:
        print("❌ 家電一覧の取得に失敗しました")
        return

    # TAKIZUMIを検索
    takizumi = None
    for appliance in appliances:
        if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == 'TAKIZUMI':
            takizumi = appliance
            break

    if not takizumi:
        print("❌ TAKIZUMI が見つかりません")
        return

    print(f"✅ TAKIZUMI検出")
    print(f"   ID: {takizumi.get('id')}")
    print(f"   Type: {takizumi.get('type')}")

    # モデル情報
    model = takizumi.get('model', {})
    print(f"\n📱 モデル情報:")
    print(f"   メーカー: {model.get('manufacturer')}")
    print(f"   モデル名: {model.get('name')}")
    print(f"   リモコン名: {model.get('remote_name')}")

    # 照明の詳細情報
    light = takizumi.get('light', {})

    print(f"\n💡 照明の状態:")
    state = light.get('state', {})
    print(f"   Power: {state.get('power')}")
    print(f"   Brightness: {state.get('brightness')}")
    print(f"   Last Button: {state.get('last_button')}")

    # ボタン一覧（詳細）
    buttons = light.get('buttons', [])

    print(f"\n🎯 ボタン一覧 ({len(buttons)}個):")
    print("="*70)

    for i, btn in enumerate(buttons, 1):
        print(f"\n{i}. {btn.get('label', '不明')}")
        print(f"   name: {btn.get('name', 'なし')}")
        print(f"   image: {btn.get('image', 'なし')}")

        # 全てのキーを表示
        for key, value in btn.items():
            if key not in ['label', 'name', 'image']:
                print(f"   {key}: {value}")

    # JSON全体をファイルに保存
    filename = "takizumi_full_data.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(takizumi, f, indent=2, ensure_ascii=False)

    print(f"\n💾 完全なデータを保存しました: {filename}")

    print("\n" + "="*70)
    print("  🔍 重要な発見")
    print("="*70)

    print(f"\n✅ 'takizumi light 202' で反応したとのこと")
    print(f"   → ボタン名 '202' を探しています...")

    found_202 = False
    for btn in buttons:
        if '202' in str(btn.get('name', '')) or '202' in str(btn.get('label', '')):
            print(f"\n🎯 見つかりました！")
            print(f"   Label: {btn.get('label')}")
            print(f"   Name: {btn.get('name')}")
            found_202 = True

    if not found_202:
        print(f"\n⚠️ '202' という名前のボタンは見つかりませんでした")
        print(f"   もしかすると:")
        print(f"   - チャンネル番号かもしれません")
        print(f"   - 別の家電のボタンかもしれません")
        print(f"   - カスタム信号かもしれません")

    print("\n" + "="*70)
    print("  📝 次のステップ")
    print("="*70)

    print("\n1. 上記のボタン一覧を確認してください")
    print("2. どのボタンで照明が反応するか教えてください")
    print("3. '202' がどこから来たのか確認します:")
    print("   - Remoアプリで確認")
    print("   - 別の家電の可能性")
    print("   - カスタム信号の可能性")


if __name__ == "__main__":
    main()
