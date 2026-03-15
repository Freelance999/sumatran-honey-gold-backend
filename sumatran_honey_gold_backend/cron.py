import logging
import requests
from django.conf import settings
from .models import WeatherObservation

api_key = settings.WUNDERGROUND_API_KEY
station_id = settings.STATION_ID
geocode = f"{settings.LATITUDE},{settings.LONGITUDE}"

logger = logging.getLogger(__name__)

def store_weather_observation():
    url = f"https://api.weather.com/v2/pws/observations/current?stationId={station_id}&format=json&units=m&apiKey={api_key}"

    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()

        obs = data['observations'][0]

        WeatherObservation.objects.create(
            station_id=obs['stationID'],
            temperature=obs['metric']['temp'],
            humidity=obs['humidity'],
            wind_speed=obs['metric']['windSpeed'],
            pressure=obs['metric']['pressure'],
            precip_rate=obs['metric']['precipRate'],
            observed_at=obs['obsTimeLocal']
        )
    else:
        logger.error(f"Error. Status code: {response.status_code}, Response: {response.text}")