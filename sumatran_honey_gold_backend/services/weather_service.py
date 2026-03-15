import requests
from django.conf import settings


class WeatherService:

    def __init__(self):
        self.wunderground_api_key = settings.WUNDERGROUND_API_KEY
        self.station_id = settings.STATION_ID
        self.openweathermap_api_key = settings.OPENWEATHERMAP_API_KEY

        self.wunderground_url = (
            f"https://api.weather.com/v2/pws/observations/current?"
            f"stationId={self.station_id}&format=json&units=m&apiKey={self.wunderground_api_key}"
        )

    def get_weather(self, latitude=None, longitude=None):
        weather_temperature = None
        weather_humidity = None
        weather_wind_speed = None

        try:
            res = requests.get(self.wunderground_url, timeout=5)
            if res.status_code == 200:
                data = res.json()

                if "observations" in data and len(data["observations"]) > 0:
                    obs = data["observations"][0]

                    weather_temperature = obs["metric"]["temp"]
                    weather_humidity = obs["humidity"]
                    weather_wind_speed = obs["metric"]["windSpeed"]

        except Exception as e:
            print(f"Wunderground error: {e}")

        if weather_temperature is None and latitude and longitude:
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather?"
                    f"lat={latitude}&lon={longitude}"
                    f"&appid={self.openweathermap_api_key}&units=metric&lang=id"
                )

                res = requests.get(url, timeout=5)

                if res.status_code == 200:
                    data = res.json()

                    weather_temperature = data["main"]["temp"]
                    weather_humidity = data["main"]["humidity"]
                    weather_wind_speed = data["wind"]["speed"]

            except Exception as e:
                print(f"OpenWeatherMap error: {e}")

        return {
            "temperature": weather_temperature,
            "humidity": weather_humidity,
            "wind_speed": weather_wind_speed,
        }