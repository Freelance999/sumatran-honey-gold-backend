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
        weather_uv = None
        weather_rain = None
        weather_latitude = None
        weather_longitude = None

        try:
            res = requests.get(self.wunderground_url, timeout=5)
            if res.status_code == 200:
                data = res.json()

                if "observations" in data and len(data["observations"]) > 0:
                    obs = data["observations"][0]

                    weather_temperature = obs["metric"]["temp"]
                    weather_humidity = obs["humidity"]
                    weather_wind_speed = obs["metric"]["windSpeed"]
                    weather_uv = obs.get("uv")
                    weather_rain = obs["metric"].get("precipRate")
                    weather_latitude = obs.get("lat")
                    weather_longitude = obs.get("lon")

        except Exception as e:
            print(f"Wunderground error: {e}")

        if latitude is not None and longitude is not None and (
            weather_temperature is None or weather_uv is None or weather_rain is None
        ):
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/weather?"
                    f"lat={latitude}&lon={longitude}"
                    f"&appid={self.openweathermap_api_key}&units=metric&lang=id"
                )

                res = requests.get(url, timeout=5)

                if res.status_code == 200:
                    data = res.json()

                    if weather_temperature is None:
                        weather_temperature = data["main"]["temp"]

                    if weather_humidity is None:
                        weather_humidity = data["main"]["humidity"]

                    if weather_wind_speed is None:
                        weather_wind_speed = round(data["wind"]["speed"] * 3.6, 2)

                    if weather_rain is None:
                        weather_rain = (data.get("rain") or {}).get("1h")

                    if weather_latitude is None:
                        weather_latitude = data["coord"]["lat"]

                    if weather_longitude is None:
                        weather_longitude = data["coord"]["lon"]

                    if weather_uv is None:
                        onecall_url = (
                            f"https://api.openweathermap.org/data/3.0/onecall?"
                            f"lat={latitude}&lon={longitude}"
                            f"&appid={self.openweathermap_api_key}&units=metric&lang=id"
                            f"&exclude=minutely,hourly,daily,alerts"
                        )
                        onecall_res = requests.get(onecall_url, timeout=5)
                        if onecall_res.status_code == 200:
                            onecall_data = onecall_res.json()
                            weather_uv = (onecall_data.get("current") or {}).get("uvi")

            except Exception as e:
                print(f"OpenWeatherMap error: {e}")

        if weather_rain is None:
            weather_rain = 0.0

        return {
            "temperature": weather_temperature,
            "humidity": weather_humidity,
            "wind_speed": weather_wind_speed,
            "wind_speed_unit": "km/h",
            "uv": weather_uv,
            "rain": weather_rain,
            "rain_unit": "mm/h",
            "latitude": weather_latitude,
            "longitude": weather_longitude,
        }
    
    @staticmethod
    def calculate_base_score(weather_data):
        score = 100

        for w in weather_data:
            temp = w.temperature
            humidity = w.humidity

            if temp < 30 or temp > 36:
                score -= 5

            if humidity > 85:
                score -= 7
            elif humidity < 40:
                score -= 5

            if w.wind_speed > 20:
                score -= 3

            if w.precip_rate > 5:
                score -= 4

        return max(score, 0)