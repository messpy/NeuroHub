#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_all_appliances.py

Nature Remo 全家電制御テスト
登録されている全家電（照明、エアコン、テレビ、扇風機など）を順番にテスト
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


def control_light(appliance_id, button):
    """照明を制御"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/light"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}
        
        data = f"button={button}".encode()
        
        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())
        
        return result
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return None


def control_aircon(appliance_id, action):
    """エアコンを制御"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/aircon_settings"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}
        
        if action == "on":
            data = "temperature=26&operation_mode=cool".encode()
        elif action == "off":
            data = "button=power-off".encode()
        else:
            return None
        
        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = json.loads(response.read().decode())
        
        return result
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return None


def control_tv(appliance_id, button):
    """テレビを制御"""
    try:
        url = f"{BASE_URL}appliances/{appliance_id}/tv"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}
        
        data = f"button={button}".encode()
        
        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request) as response:
            result = response.read().decode()
        
        return result
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return None


def send_ir_signal(signal_id):
    """IR信号を送信（汎用家電用）"""
    try:
        url = f"{BASE_URL}signals/{signal_id}/send"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}
        
        request = Request(url, headers=headers, method='POST')
        with urlopen(request) as response:
            result = response.read().decode()
        
        return True
    except HTTPError as e:
        if e.code == 404:
            print(f"   ⚠️ 信号ID {signal_id} が見つかりません")
        else:
            print(f"   ❌ HTTPエラー: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return False


def get_ir_signals(appliance):
    """IR家電の信号一覧を取得"""
    signals = appliance.get('signals', [])
    return signals


def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("  🏠 Nature Remo 全家電制御テスト")
    print("="*70)
    
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
    
    # 家電をタイプ別に分類
    lights = []
    aircons = []
    tvs = []
    ir_devices = []
    
    for appliance in appliances:
        app_type = appliance.get('type')
        
        if app_type == 'LIGHT':
            lights.append(appliance)
        elif app_type == 'AC':
            aircons.append(appliance)
        elif app_type == 'TV':
            tvs.append(appliance)
        elif app_type == 'IR':
            ir_devices.append(appliance)
    
    print("\n📊 家電の内訳:")
    print(f"  💡 照明: {len(lights)}個")
    print(f"  ❄️ エアコン: {len(aircons)}個")
    print(f"  📺 テレビ: {len(tvs)}個")
    print(f"  🎛️ IR機器: {len(ir_devices)}個")
    
    # エアコンテスト
    if aircons:
        print("\n" + "="*70)
        print("  ❄️ エアコン制御テスト")
        print("="*70)
        
        for i, ac in enumerate(aircons, 1):
            print(f"\n{i}. {ac.get('nickname')}")
            
            # ONテスト
            print("   📤 ON送信中（冷房26度）...")
            result_on = control_aircon(ac.get('id'), "on")
            
            if result_on:
                print(f"   ✅ ON成功: temp={result_on.get('temp')}°C, mode={result_on.get('mode')}")
                print("   💡 エアコンが起動しましたか？（5秒観察）")
                time.sleep(5)
            
            # OFFテスト
            print("   📤 OFF送信中...")
            result_off = control_aircon(ac.get('id'), "off")
            
            if result_off:
                print(f"   ✅ OFF成功")
                print("   💡 エアコンが停止しましたか？")
            
            time.sleep(3)
    
    # テレビテスト
    if tvs:
        print("\n" + "="*70)
        print("  📺 テレビ制御テスト")
        print("="*70)
        
        for i, tv in enumerate(tvs, 1):
            print(f"\n{i}. {tv.get('nickname')}")
            
            # 電源ボタン
            print("   📤 電源ボタン送信中...")
            result = control_tv(tv.get('id'), "power")
            
            if result:
                print(f"   ✅ 電源ボタン送信成功")
                print("   💡 テレビの電源が切り替わりましたか？")
            
            time.sleep(5)
    
    # IR機器テスト
    if ir_devices:
        print("\n" + "="*70)
        print("  🎛️ IR機器制御テスト")
        print("="*70)
        
        for i, device in enumerate(ir_devices, 1):
            nickname = device.get('nickname')
            print(f"\n{i}. {nickname}")
            
            # 登録されている信号を取得
            signals = get_ir_signals(device)
            
            if signals:
                print(f"   登録信号数: {len(signals)}個")
                
                # 最初の3つの信号を試す
                for j, signal in enumerate(signals[:3], 1):
                    signal_name = signal.get('name', '不明')
                    signal_id = signal.get('id')
                    
                    print(f"\n   {j}. {signal_name}")
                    print(f"      📤 信号送信中...")
                    
                    if send_ir_signal(signal_id):
                        print(f"      ✅ 送信成功")
                        print(f"      💡 {nickname}が反応しましたか？")
                        time.sleep(3)
            else:
                print(f"   ⚠️ 登録されている信号がありません")
    
    # 照明テスト（最後に実行、レート制限回避）
    if lights:
        print("\n" + "="*70)
        print("  💡 照明制御テスト（ゆっくり実行）")
        print("="*70)
        
        for i, light in enumerate(lights, 1):
            print(f"\n{i}. {light.get('nickname')}")
            
            # 10秒待機（レート制限回避）
            print("   ⏳ 10秒待機（レート制限回避）...")
            time.sleep(10)
            
            # ONテスト
            print("   📤 ON送信中...")
            result_on = control_light(light.get('id'), "on")
            
            if result_on:
                print(f"   ✅ ON成功: power={result_on.get('power')}")
                print("   💡 照明が点きましたか？")
            
            time.sleep(10)
            
            # OFFテスト
            print("   📤 OFF送信中...")
            result_off = control_light(light.get('id'), "off")
            
            if result_off:
                print(f"   ✅ OFF成功: power={result_off.get('power')}")
                print("   💡 照明が消えましたか？")
    
    print("\n" + "="*70)
    print("  ✅ 全家電テスト完了")
    print("="*70)
    
    print("\n📊 結果を教えてください:")
    print("  1. エアコンは動きましたか？")
    print("  2. テレビは動きましたか？")
    print("  3. 扇風機などIR機器は動きましたか？")
    print("  4. 照明は動きましたか？")
    print("  5. Remoのランプは点滅しましたか？")


if __name__ == "__main__":
    main()
