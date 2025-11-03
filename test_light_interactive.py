#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_light_interactive.py

Nature Remo 照明制御テスト（対話型）
ユーザーが選択して照明を制御
"""

import os
import sys
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
    print("  💡 Nature Remo 照明制御テスト（対話型）")
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

    print(f"\n🎯 利用可能なボタン:")
    button_list = []
    for i, btn in enumerate(buttons, 1):
        label = btn.get('label')
        name = btn.get('name')
        button_list.append((name, label))
        print(f"  {i}. {label} (name: {name})")

    # 対話型制御
    print("\n" + "=" * 60)
    print("  照明を制御します")
    print("=" * 60)

    while True:
        print("\n選択してください:")
        print("  1. ON  - 照明をつける")
        print("  2. OFF - 照明を消す")
        print("  3. All - 全灯")
        print("  4. Night - 常夜灯")
        print("  5. Bright - 明るく")
        print("  6. Dark - 暗く")
        print("  0. 終了")

        try:
            choice = input("\n選択 (0-6): ").strip()

            if choice == "0":
                print("\n👋 終了します")
                break

            choice_num = int(choice)

            if 1 <= choice_num <= len(button_list):
                button_name, button_label = button_list[choice_num - 1]

                print(f"\n🎛️ {button_label} を実行中...")

                if control_light(light, button_name):
                    if button_name == "on":
                        print("✅ 💡 照明をONにしました")
                    elif button_name == "off":
                        print("✅ 🌙 照明をOFFにしました")
                    elif button_name == "on-100":
                        print("✅ 🔆 全灯にしました")
                    elif button_name == "night":
                        print("✅ 🌙 常夜灯にしました")
                    elif button_name == "bright-up":
                        print("✅ ⬆️ 明るくしました")
                    elif button_name == "bright-down":
                        print("✅ ⬇️ 暗くしました")
                    else:
                        print(f"✅ {button_label} を実行しました")
                else:
                    print("❌ 制御に失敗しました")
            else:
                print("❌ 無効な選択です")

        except ValueError:
            print("❌ 数字を入力してください")
        except KeyboardInterrupt:
            print("\n\n👋 終了します")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")

    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
