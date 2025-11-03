#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weather_agent.py - 天気予報エージェント
- git_agentと同様のインターフェース
- APIキー不要（Open-Meteo + ip-api + Nominatim）
- wether_core.pyの機能を統合
"""

import sys
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
import yaml
import json
import re

# プロジェクトルート
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.common import BaseAgent

# デフォルト設定
DEFAULT_LAT = 35.68  # 東京
DEFAULT_LON = 139.76
UA = "NeuroHub/1.0 (weather tool; contact: you@example.com)"
TIMEOUT = 10

# 天気コードマッピング
WEATHER_CODES = {
    0: ("晴れ", "☀️"),
    1: ("ほぼ晴れ", "🌤️"),
    2: ("部分的に曇り", "⛅"),
    3: ("曇り", "☁️"),
    45: ("霧", "🌫️"),
    48: ("霧氷", "🌫️"),
    51: ("小雨", "🌦️"),
    53: ("雨", "🌧️"),
    55: ("大雨", "🌧️"),
    56: ("凍雨", "🌨️"),
    57: ("凍雨（強）", "🌨️"),
    61: ("小雨", "🌦️"),
    63: ("雨", "🌧️"),
    65: ("大雨", "🌧️"),
    66: ("凍雨", "🌨️"),
    67: ("凍雨（強）", "🌨️"),
    71: ("小雪", "🌨️"),
    73: ("雪", "❄️"),
    75: ("大雪", "❄️"),
    77: ("霰", "🌨️"),
    80: ("にわか雨", "🌦️"),
    81: ("にわか雨（強）", "🌧️"),
    82: ("激しいにわか雨", "🌧️"),
    85: ("にわか雪", "🌨️"),
    86: ("にわか雪（強）", "❄️"),
    95: ("雷雨", "⛈️"),
    96: ("雷雨（雹）", "⛈️"),
    99: ("激しい雷雨（雹）", "⛈️"),
}

class WeatherAgent(BaseAgent):
    """天気予報エージェント"""

    def __init__(self, timeout: float = TIMEOUT):
        # BaseAgent初期化
        super().__init__("weather_agent")

        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": UA})

    def execute(self, prompt: str) -> str:
        """Execute weather query based on prompt.

        Args:
            prompt: User prompt (e.g., "今日の天気", "明日の予報")

        Returns:
            Weather information
        """
        try:
            # Get location
            lat, lon, location_name = self.get_location_from_ip()

            # Get forecast
            forecast = self.get_forecast(lat, lon)

            if not forecast:
                return "⚠️ Failed to get weather data"

            # Format result
            result = f"📍 {location_name}\n\n"

            # Current weather
            if 'current' in forecast:
                current = forecast['current']
                weather_desc, emoji = self.get_weather_description(current.get('weather_code', 0))
                result += f"🌡️ 現在: {current.get('temperature_2m', 'N/A')}°C {emoji} {weather_desc}\n"
                result += f"💨 風速: {current.get('wind_speed_10m', 'N/A')} km/h\n\n"

            # Today's forecast
            if 'daily' in forecast:
                daily = forecast['daily']
                if daily['time']:
                    today = daily['time'][0]
                    result += f"📅 今日 ({today}):\n"
                    result += f"  🌡️ 最高: {daily['temperature_2m_max'][0]}°C\n"
                    result += f"  🌡️ 最低: {daily['temperature_2m_min'][0]}°C\n"

                    if len(daily['time']) > 1:
                        tomorrow = daily['time'][1]
                        result += f"\n📅 明日 ({tomorrow}):\n"
                        result += f"  🌡️ 最高: {daily['temperature_2m_max'][1]}°C\n"
                        result += f"  🌡️ 最低: {daily['temperature_2m_min'][1]}°C\n"

            return result

        except Exception as e:
            self.handle_error(e, "Weather query")
            return f"❌ Error: {e}"

    def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get comprehensive forecast data including current and daily."""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
                "forecast_days": 7,
                "timezone": "auto"
            }
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            return data

        except Exception as e:
            self.logger.error(f"Failed to get forecast: {e}")
            return {}

    def get_location_from_ip(self) -> Tuple[float, float, str]:
        """IPアドレスから位置を取得"""
        try:
            url = "http://ip-api.com/json/?fields=lat,lon,city,country,status"
            r = self.session.get(url, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            if data.get("status") == "success":
                lat = data.get("lat", DEFAULT_LAT)
                lon = data.get("lon", DEFAULT_LON)
                city = data.get("city", "Unknown")
                country = data.get("country", "")
                location_name = f"{city}, {country}" if country else city
                return lat, lon, location_name
            else:
                return DEFAULT_LAT, DEFAULT_LON, "Tokyo, Japan"

        except Exception:
            return DEFAULT_LAT, DEFAULT_LON, "Tokyo, Japan"

    def get_weather_description(self, weather_code: int) -> Tuple[str, str]:
        """Get weather description and emoji from code.

        Args:
            weather_code: Weather code from API

        Returns:
            Tuple of (description, emoji)
        """
        return WEATHER_CODES.get(weather_code, ("不明", "❓"))

    def reverse_geocode(self, lat: float, lon: float) -> str:
        """緯度経度から地名を取得"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "format": "jsonv2",
                "lat": lat,
                "lon": lon,
                "zoom": 10,
                "accept-language": "ja",
            }
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            display_name = data.get("display_name", f"lat:{lat}, lon:{lon}")
            return display_name.split(",")[0]  # 最初の部分のみ

        except Exception:
            return f"lat:{lat}, lon:{lon}"

    def get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """現在の天気を取得"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
                "timezone": "auto"
            }
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            current = data.get("current", {})
            weather_code = current.get("weather_code", 0)
            weather_desc, weather_emoji = WEATHER_CODES.get(weather_code, ("不明", "❓"))

            return {
                "temperature": current.get("temperature_2m"),
                "weather_code": weather_code,
                "weather_description": weather_desc,
                "weather_emoji": weather_emoji,
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "time": current.get("time"),
                "units": data.get("current_units", {})
            }

        except Exception as e:
            return {"error": str(e)}

    def get_hourly_forecast(self, lat: float, lon: float, hours: int = 24) -> Dict[str, Any]:
        """時間予報を取得"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,weather_code,precipitation_probability",
                "forecast_days": 2,
                "timezone": "auto"
            }
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            codes = hourly.get("weather_code", [])
            probs = hourly.get("precipitation_probability", [])

            forecasts = []
            for i in range(min(hours, len(times))):
                weather_code = codes[i] if i < len(codes) else 0
                weather_desc, weather_emoji = WEATHER_CODES.get(weather_code, ("不明", "❓"))

                forecasts.append({
                    "time": times[i],
                    "temperature": temps[i] if i < len(temps) else None,
                    "weather_code": weather_code,
                    "weather_description": weather_desc,
                    "weather_emoji": weather_emoji,
                    "precipitation_probability": probs[i] if i < len(probs) else None
                })

            return {
                "forecasts": forecasts,
                "units": data.get("hourly_units", {})
            }

        except Exception as e:
            return {"error": str(e)}

    def get_daily_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """日次予報を取得"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
                "forecast_days": days,
                "timezone": "auto"
            }
            r = self.session.get(url, params=params, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()

            daily = data.get("daily", {})
            times = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            codes = daily.get("weather_code", [])
            probs = daily.get("precipitation_probability_max", [])

            forecasts = []
            for i in range(min(days, len(times))):
                weather_code = codes[i] if i < len(codes) else 0
                weather_desc, weather_emoji = WEATHER_CODES.get(weather_code, ("不明", "❓"))

                forecasts.append({
                    "date": times[i],
                    "temperature_max": max_temps[i] if i < len(max_temps) else None,
                    "temperature_min": min_temps[i] if i < len(min_temps) else None,
                    "weather_code": weather_code,
                    "weather_description": weather_desc,
                    "weather_emoji": weather_emoji,
                    "precipitation_probability": probs[i] if i < len(probs) else None
                })

            return {
                "forecasts": forecasts,
                "units": data.get("daily_units", {})
            }

        except Exception as e:
            return {"error": str(e)}

    def get_weather_report(self, lat: Optional[float] = None, lon: Optional[float] = None,
                          forecast_type: str = "current") -> Dict[str, Any]:
        """天気レポートを取得"""
        # 位置の決定
        if lat is None or lon is None:
            lat, lon, location_name = self.get_location_from_ip()
        else:
            location_name = self.reverse_geocode(lat, lon)

        result = {
            "location": {
                "name": location_name,
                "latitude": lat,
                "longitude": lon
            },
            "timestamp": datetime.datetime.now().isoformat()
        }

        # 天気データ取得
        if forecast_type == "current":
            result["current_weather"] = self.get_current_weather(lat, lon)
        elif forecast_type == "hourly":
            result["hourly_forecast"] = self.get_hourly_forecast(lat, lon)
        elif forecast_type == "daily":
            result["daily_forecast"] = self.get_daily_forecast(lat, lon)
        elif forecast_type == "all":
            result["current_weather"] = self.get_current_weather(lat, lon)
            result["hourly_forecast"] = self.get_hourly_forecast(lat, lon, 12)
            result["daily_forecast"] = self.get_daily_forecast(lat, lon, 3)

        return result

def main():
    parser = argparse.ArgumentParser(description="天気予報エージェント")
    parser.add_argument("--lat", type=float, help="緯度")
    parser.add_argument("--lon", type=float, help="経度")
    parser.add_argument("--type", choices=["current", "hourly", "daily", "all"],
                       default="current", help="予報タイプ")
    parser.add_argument("--hours", type=int, default=24, help="時間予報の時間数")
    parser.add_argument("--days", type=int, default=7, help="日次予報の日数")
    parser.add_argument("--output", action="store_true", help="結果をファイルに保存")
    parser.add_argument("--format", choices=["yaml", "json"], default="yaml", help="出力形式")

    args = parser.parse_args()

    # 天気エージェント実行
    agent = WeatherAgent()
    result = agent.get_weather_report(args.lat, args.lon, args.type)

    # 出力
    if args.output:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        location_safe = re.sub(r'[^\w\-_.]', '_', result["location"]["name"])
        filename = f"weather_{location_safe}_{timestamp}.{args.format}"

        with open(filename, 'w', encoding='utf-8') as f:
            if args.format == "yaml":
                yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            else:
                json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"天気レポートを保存しました: {filename}")
    else:
        if args.format == "yaml":
            yaml.dump(result, sys.stdout, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
