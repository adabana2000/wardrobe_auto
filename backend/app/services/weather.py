"""
天気API統合サービス
OpenWeatherMap APIを使用して天気情報を取得
"""

from typing import Dict, Optional
from datetime import date, datetime, timedelta
import requests
import logging
import os
import json

logger = logging.getLogger(__name__)


class WeatherService:
    """
    OpenWeatherMap APIを使用した天気サービス
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(
        self, city: str = "Tokyo", country_code: str = "JP"
    ) -> Dict:
        """
        現在の天気を取得

        Args:
            city: 都市名
            country_code: 国コード

        Returns:
            Dict: 天気情報
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not set. Using mock data.")
            return self._get_mock_weather()

        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric",  # 摂氏
                "lang": "ja",
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._parse_weather_data(data)
            else:
                logger.error(f"Weather API error: {response.status_code}")
                return self._get_mock_weather()

        except Exception as e:
            logger.error(f"Failed to fetch weather: {e}")
            return self._get_mock_weather()

    def get_forecast(
        self, city: str = "Tokyo", country_code: str = "JP", days: int = 5
    ) -> list[Dict]:
        """
        天気予報を取得

        Args:
            city: 都市名
            country_code: 国コード
            days: 予報日数

        Returns:
            List[Dict]: 天気予報のリスト
        """
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not set. Using mock data.")
            return [self._get_mock_weather() for _ in range(days)]

        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric",
                "lang": "ja",
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._parse_forecast_data(data, days)
            else:
                logger.error(f"Forecast API error: {response.status_code}")
                return [self._get_mock_weather() for _ in range(days)]

        except Exception as e:
            logger.error(f"Failed to fetch forecast: {e}")
            return [self._get_mock_weather() for _ in range(days)]

    def _parse_weather_data(self, data: Dict) -> Dict:
        """
        OpenWeatherMapレスポンスをパース

        Args:
            data: APIレスポンス

        Returns:
            Dict: パースされた天気情報
        """
        return {
            "date": date.today().isoformat(),
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "humidity": data["main"]["humidity"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "icon": data["weather"][0]["icon"],
        }

    def _parse_forecast_data(self, data: Dict, days: int) -> list[Dict]:
        """
        天気予報データをパース

        Args:
            data: APIレスポンス
            days: 取得日数

        Returns:
            List[Dict]: 日別の天気予報
        """
        forecasts = []
        daily_data = {}

        # 3時間ごとのデータを日別に集約
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            day = dt.date().isoformat()

            if day not in daily_data:
                daily_data[day] = {
                    "temps": [],
                    "conditions": [],
                    "humidity": [],
                    "wind_speed": [],
                }

            daily_data[day]["temps"].append(item["main"]["temp"])
            daily_data[day]["conditions"].append(item["weather"][0]["main"])
            daily_data[day]["humidity"].append(item["main"]["humidity"])
            daily_data[day]["wind_speed"].append(item["wind"]["speed"])

        # 日別に平均・最頻値を計算
        for day, values in list(daily_data.items())[:days]:
            forecast = {
                "date": day,
                "temp": round(sum(values["temps"]) / len(values["temps"]), 1),
                "temp_min": round(min(values["temps"]), 1),
                "temp_max": round(max(values["temps"]), 1),
                "condition": max(set(values["conditions"]), key=values["conditions"].count),
                "humidity": round(sum(values["humidity"]) / len(values["humidity"])),
                "wind_speed": round(sum(values["wind_speed"]) / len(values["wind_speed"]), 1),
            }
            forecasts.append(forecast)

        return forecasts

    def _get_mock_weather(self) -> Dict:
        """
        モックの天気データを返す

        Returns:
            Dict: モック天気情報
        """
        return {
            "date": date.today().isoformat(),
            "temp": 20.0,
            "feels_like": 18.0,
            "temp_min": 15.0,
            "temp_max": 25.0,
            "humidity": 60,
            "condition": "Clear",
            "description": "晴れ",
            "wind_speed": 3.5,
            "icon": "01d",
        }

    def should_wear_outer(self, weather_data: Dict) -> bool:
        """
        アウターが必要かどうか判定

        Args:
            weather_data: 天気データ

        Returns:
            bool: アウターが必要ならTrue
        """
        temp = weather_data.get("temp", 20)
        condition = weather_data.get("condition", "Clear")

        # 気温が15度以下、または雨の場合はアウターが必要
        if temp < 15 or condition in ["Rain", "Drizzle", "Thunderstorm"]:
            return True

        return False

    def should_wear_rainwear(self, weather_data: Dict) -> bool:
        """
        雨具が必要かどうか判定

        Args:
            weather_data: 天気データ

        Returns:
            bool: 雨具が必要ならTrue
        """
        condition = weather_data.get("condition", "Clear")
        return condition in ["Rain", "Drizzle", "Thunderstorm"]

    def get_clothing_recommendation(self, weather_data: Dict) -> Dict:
        """
        天気に基づく衣類推奨情報

        Args:
            weather_data: 天気データ

        Returns:
            Dict: 推奨情報
        """
        temp = weather_data.get("temp", 20)
        condition = weather_data.get("condition", "Clear")

        recommendation = {
            "needs_outer": self.should_wear_outer(weather_data),
            "needs_rainwear": self.should_wear_rainwear(weather_data),
            "suggested_material": "",
            "suggested_style": "",
        }

        # 気温に基づく素材推奨
        if temp < 10:
            recommendation["suggested_material"] = "ウール、フリース"
            recommendation["suggested_style"] = "厚手のアウター"
        elif temp < 15:
            recommendation["suggested_material"] = "綿、ポリエステル"
            recommendation["suggested_style"] = "ジャケット、カーディガン"
        elif temp < 25:
            recommendation["suggested_material"] = "綿"
            recommendation["suggested_style"] = "長袖シャツ"
        else:
            recommendation["suggested_material"] = "リネン、薄手の綿"
            recommendation["suggested_style"] = "半袖、軽装"

        return recommendation
