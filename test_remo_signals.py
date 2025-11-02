#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_remo_signals.py

Nature Remo 信号送信確認テスト
各ボタンを順番に試してどれが動作するか確認
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


def send_signal(appliance, button_name):
    """信号送信"""
    try:
        device_id = appliance.get('id')
        url = f"{BASE_URL}appliances/{device_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}
        
        data = f"button={button_name}".encode()
        
        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = loads(response.read().decode())
        
        return result
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  📡 Nature Remo 全ボタンテスト")
    print("="*60)
    
    print("\n🔍 TAKIZUMI検索中...")
    light = get_light()
    
    if not light:
        print("❌ TAKIZUMI が見つかりません")
        return
    
    print(f"✅ 照明検出: {light.get('nickname')}")
    
    # ボタン一覧
    light_data = light.get('light', {})
    buttons = light_data.get('buttons', [])
    
    print(f"\n🎯 利用可能なボタン: {len(buttons)}個")
    for i, btn in enumerate(buttons, 1):
        print(f"  {i}. {btn.get('label')} (name: {btn.get('name')})")
    
    print("\n" + "="*60)
    print("  全ボタンを順番に実行します")
    print("  各ボタン実行後、照明が反応するか確認してください")
    print("="*60)
    
    input("\nEnterキーを押して開始...")
    
    # 全ボタンを順番に実行
    for i, btn in enumerate(buttons, 1):
        label = btn.get('label')
        name = btn.get('name')
        
        print(f"\n{'='*60}")
        print(f"  {i}/{len(buttons)}: {label} (name: {name})")
        print(f"{'='*60}")
        
        print(f"\n🎛️ 信号送信中...")
        result = send_signal(light, name)
        
        if result:
            print(f"✅ API成功:")
            print(f"   power: {result.get('power')}")
            print(f"   brightness: {result.get('brightness')}")
            print(f"   last_button: {result.get('last_button')}")
            
            print(f"\n💡 照明は反応しましたか？")
            print(f"   このボタン({label})で照明が動作したか確認してください")
        else:
            print(f"❌ API失敗")
        
        if i < len(buttons):
            print(f"\n⏳ 次のボタンまで3秒待機...")
            time.sleep(3)
    
    print("\n" + "="*60)
    print("  ✅ 全ボタンテスト完了")
    print("="*60)
    
    print("\n📊 結果まとめ:")
    print("   どのボタンで照明が反応しましたか？")
    print("")
    for i, btn in enumerate(buttons, 1):
        print(f"  {i}. {btn.get('label')} (name: {btn.get('name')}) - [ ] 反応した")
    
    print("\n💡 次のステップ:")
    print("   1. 反応したボタンを確認")
    print("   2. 反応しなかった場合、Remoアプリで再学習")
    print("   3. Remoデバイスと照明の位置を確認")
    print("   4. Remoデバイスのランプが点滅したか確認")


if __name__ == "__main__":
    main()
