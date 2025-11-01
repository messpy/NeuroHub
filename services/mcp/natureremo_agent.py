#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
natureremo_agent.py

NatureRemo API統合エージェント
TASK_MANAGEMENT.md要件対応:
- .env環境変数からのNatureRemo API実行
- スマートホーム制御をMCPシステムに統合
"""

from __future__ import annotations
import os
import sys
import json
import asyncio
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.llm.llm_common import load_env_from_config

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NatureRemoDevice:
    """NatureRemoデバイス情報"""
    id: str
    name: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illumination: Optional[float] = None
    movement: Optional[bool] = None

@dataclass
class NatureRemoAppliance:
    """NatureRemo家電情報"""
    id: str
    nickname: str
    type: str
    model: Optional[str] = None
    device_id: Optional[str] = None

class NatureRemoAgent:
    """
    NatureRemo API統合エージェント

    機能:
    - デバイス情報取得
    - 家電制御
    - センサーデータ取得
    - 環境変数からのAPI設定
    """

    def __init__(self):
        # 環境変数読み込み
        load_env_from_config()

        # NatureRemo API設定
        self.api_token = os.getenv('NATUREREMO_API_TOKEN')
        self.base_url = 'https://api.nature.global'

        # APIヘッダー設定
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        # 接続テスト
        self.connected = self._test_connection()

        if self.connected:
            logger.info("🏠 NatureRemo API接続成功")
        else:
            logger.warning("⚠️ NatureRemo API接続失敗 - トークンを確認してください")

    def _test_connection(self) -> bool:
        """API接続テスト"""
        if not self.api_token:
            logger.warning("NATUREREMO_API_TOKEN が設定されていません")
            return False

        try:
            response = requests.get(
                f"{self.base_url}/1/users/me",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"API接続テスト失敗: {e}")
            return False

    async def get_devices(self) -> List[NatureRemoDevice]:
        """デバイス一覧取得"""
        if not self.connected:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/1/devices",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            devices = []
            for device_data in response.json():
                device = NatureRemoDevice(
                    id=device_data['id'],
                    name=device_data['name'],
                    temperature=device_data.get('newest_events', {}).get('te', {}).get('val'),
                    humidity=device_data.get('newest_events', {}).get('hu', {}).get('val'),
                    illumination=device_data.get('newest_events', {}).get('il', {}).get('val'),
                    movement=device_data.get('newest_events', {}).get('mo', {}).get('val')
                )
                devices.append(device)

            logger.info(f"📱 デバイス取得成功: {len(devices)}台")
            return devices

        except Exception as e:
            logger.error(f"デバイス取得エラー: {e}")
            return []

    async def get_appliances(self) -> List[NatureRemoAppliance]:
        """家電一覧取得"""
        if not self.connected:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/1/appliances",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            appliances = []
            for app_data in response.json():
                appliance = NatureRemoAppliance(
                    id=app_data['id'],
                    nickname=app_data['nickname'],
                    type=app_data['type'],
                    model=app_data.get('model', {}).get('name'),
                    device_id=app_data.get('device', {}).get('id')
                )
                appliances.append(appliance)

            logger.info(f"🏠 家電取得成功: {len(appliances)}台")
            return appliances

        except Exception as e:
            logger.error(f"家電取得エラー: {e}")
            return []

    async def get_sensor_data(self) -> Dict[str, Any]:
        """センサーデータ取得"""
        devices = await self.get_devices()

        sensor_data = {
            'timestamp': datetime.now().isoformat(),
            'devices': [],
            'summary': {
                'avg_temperature': None,
                'avg_humidity': None,
                'total_devices': len(devices)
            }
        }

        temperatures = []
        humidities = []

        for device in devices:
            device_info = {
                'id': device.id,
                'name': device.name,
                'temperature': device.temperature,
                'humidity': device.humidity,
                'illumination': device.illumination,
                'movement': device.movement
            }
            sensor_data['devices'].append(device_info)

            if device.temperature is not None:
                temperatures.append(device.temperature)
            if device.humidity is not None:
                humidities.append(device.humidity)

        # 平均値計算
        if temperatures:
            sensor_data['summary']['avg_temperature'] = sum(temperatures) / len(temperatures)
        if humidities:
            sensor_data['summary']['avg_humidity'] = sum(humidities) / len(humidities)

        return sensor_data

    async def control_appliance(self, appliance_id: str, signal: str) -> Dict[str, Any]:
        """家電制御"""
        if not self.connected:
            return {
                'status': 'error',
                'message': 'API未接続'
            }

        try:
            # シンプルな制御（実際の使用時は適切なシグナルを指定）
            data = {'signal': signal}

            response = requests.post(
                f"{self.base_url}/1/appliances/{appliance_id}/signals",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()

            return {
                'status': 'success',
                'appliance_id': appliance_id,
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"家電制御エラー: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'appliance_id': appliance_id
            }

    async def get_air_conditioner_settings(self, appliance_id: str) -> Dict[str, Any]:
        """エアコン設定取得"""
        if not self.connected:
            return {}

        try:
            response = requests.get(
                f"{self.base_url}/1/appliances/{appliance_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            appliance_data = response.json()
            if appliance_data.get('type') == 'AC':
                settings = appliance_data.get('settings', {})
                return {
                    'temperature': settings.get('temp'),
                    'mode': settings.get('mode'),
                    'volume': settings.get('vol'),
                    'direction': settings.get('dir'),
                    'power': 'on' if settings.get('button') != 'power-off' else 'off'
                }

            return {}

        except Exception as e:
            logger.error(f"エアコン設定取得エラー: {e}")
            return {}

    async def set_air_conditioner(self, appliance_id: str, temperature: Optional[int] = None,
                                mode: Optional[str] = None, power: Optional[bool] = None) -> Dict[str, Any]:
        """エアコン設定"""
        if not self.connected:
            return {
                'status': 'error',
                'message': 'API未接続'
            }

        try:
            # 設定データ構築
            settings = {}
            if temperature is not None:
                settings['temperature'] = str(temperature)
            if mode is not None:
                settings['operation_mode'] = mode
            if power is not None:
                settings['button'] = 'power-on' if power else 'power-off'

            response = requests.post(
                f"{self.base_url}/1/appliances/{appliance_id}/aircon_settings",
                headers=self.headers,
                json=settings,
                timeout=10
            )
            response.raise_for_status()

            return {
                'status': 'success',
                'appliance_id': appliance_id,
                'settings': settings,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"エアコン設定エラー: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'appliance_id': appliance_id
            }

    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """包括的なステータス取得"""
        devices = await self.get_devices()
        appliances = await self.get_appliances()
        sensor_data = await self.get_sensor_data()

        status = {
            'timestamp': datetime.now().isoformat(),
            'connection_status': 'connected' if self.connected else 'disconnected',
            'devices': {
                'count': len(devices),
                'list': [{'id': d.id, 'name': d.name} for d in devices]
            },
            'appliances': {
                'count': len(appliances),
                'list': [{'id': a.id, 'nickname': a.nickname, 'type': a.type} for a in appliances]
            },
            'environment': {
                'avg_temperature': sensor_data['summary']['avg_temperature'],
                'avg_humidity': sensor_data['summary']['avg_humidity']
            },
            'recommendations': []
        }

        # 推奨アクション生成
        if sensor_data['summary']['avg_temperature']:
            temp = sensor_data['summary']['avg_temperature']
            if temp > 28:
                status['recommendations'].append("気温が高いです。エアコンの利用を検討してください。")
            elif temp < 18:
                status['recommendations'].append("気温が低いです。暖房の利用を検討してください。")

        if sensor_data['summary']['avg_humidity']:
            humidity = sensor_data['summary']['avg_humidity']
            if humidity > 70:
                status['recommendations'].append("湿度が高いです。除湿を検討してください。")
            elif humidity < 30:
                status['recommendations'].append("湿度が低いです。加湿を検討してください。")

        return status


# CLIインターフェース
async def main():
    """NatureRemoエージェントのCLI実行"""
    import argparse

    parser = argparse.ArgumentParser(description="NatureRemo API統合エージェント")
    parser.add_argument('command', choices=[
        'devices', 'appliances', 'sensors', 'status', 'control', 'ac-get', 'ac-set'
    ], help='実行するコマンド')
    parser.add_argument('--appliance-id', help='家電ID (control, ac-get, ac-set用)')
    parser.add_argument('--signal', help='制御シグナル (control用)')
    parser.add_argument('--temperature', type=int, help='温度設定 (ac-set用)')
    parser.add_argument('--mode', help='運転モード (ac-set用)')
    parser.add_argument('--power', type=bool, help='電源設定 (ac-set用)')
    parser.add_argument('--output', choices=['json', 'summary'], default='summary',
                       help='出力形式')

    args = parser.parse_args()

    agent = NatureRemoAgent()

    try:
        result = None

        if args.command == 'devices':
            devices = await agent.get_devices()
            result = [{'id': d.id, 'name': d.name, 'temperature': d.temperature,
                     'humidity': d.humidity} for d in devices]

        elif args.command == 'appliances':
            appliances = await agent.get_appliances()
            result = [{'id': a.id, 'nickname': a.nickname, 'type': a.type,
                     'model': a.model} for a in appliances]

        elif args.command == 'sensors':
            result = await agent.get_sensor_data()

        elif args.command == 'status':
            result = await agent.get_comprehensive_status()

        elif args.command == 'control':
            if not args.appliance_id or not args.signal:
                print("Error: --appliance-id と --signal が必要です")
                return 1
            result = await agent.control_appliance(args.appliance_id, args.signal)

        elif args.command == 'ac-get':
            if not args.appliance_id:
                print("Error: --appliance-id が必要です")
                return 1
            result = await agent.get_air_conditioner_settings(args.appliance_id)

        elif args.command == 'ac-set':
            if not args.appliance_id:
                print("Error: --appliance-id が必要です")
                return 1
            result = await agent.set_air_conditioner(
                args.appliance_id, args.temperature, args.mode, args.power
            )

        if args.output == 'json':
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # サマリー形式での出力
            if args.command == 'devices':
                print(f"\n📱 NatureRemoデバイス一覧")
                print(f"=" * 40)
                for device in result:
                    print(f"🔹 {device['name']} (ID: {device['id']})")
                    if device['temperature']:
                        print(f"   🌡️ 温度: {device['temperature']}°C")
                    if device['humidity']:
                        print(f"   💧 湿度: {device['humidity']}%")

            elif args.command == 'appliances':
                print(f"\n🏠 家電一覧")
                print(f"=" * 40)
                for appliance in result:
                    print(f"🔹 {appliance['nickname']} ({appliance['type']})")
                    print(f"   ID: {appliance['id']}")
                    if appliance['model']:
                        print(f"   モデル: {appliance['model']}")

            elif args.command == 'status':
                print(f"\n🏠 NatureRemo総合ステータス")
                print(f"=" * 40)
                print(f"接続状態: {result['connection_status']}")
                print(f"デバイス数: {result['devices']['count']}台")
                print(f"家電数: {result['appliances']['count']}台")
                if result['environment']['avg_temperature']:
                    print(f"平均気温: {result['environment']['avg_temperature']:.1f}°C")
                if result['environment']['avg_humidity']:
                    print(f"平均湿度: {result['environment']['avg_humidity']:.1f}%")
                if result['recommendations']:
                    print(f"\n💡 推奨アクション:")
                    for rec in result['recommendations']:
                        print(f"  • {rec}")

            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))

        return 0

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    asyncio.run(main())
