import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser

api_key = settings.WUNDERGROUND_API_KEY
station_id = settings.STATION_ID
geocode = f"{settings.LATITUDE},{settings.LONGITUDE}"
openweathermap_api_key = settings.OPENWEATHERMAP_API_KEY

class WeatherViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["fetch_forecasts", "fetch_weather_station"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in []:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="forecasts")
    def fetch_forecasts(self, request):
        url = f"https://api.weather.com/v3/wx/forecast/daily/5day?geocode={geocode}&format=json&units=m&language=id-ID&apiKey={api_key}"

        try:
            response = requests.get(url)
            data = response.json()
            
            forecast_list = []
            for i in range(len(data['dayOfWeek'])):
                forecast_list.append({
                    "day": data['dayOfWeek'][i],
                    "date": data['validTimeLocal'][i],
                    "max_temperature": data['temperatureMax'][i],
                    "min_temperature": data['temperatureMin'][i],
                    "narrative": data['narrative'][i],
                    "rain_chance": data['daypart'][0]['precipChance'][i*2],
                })

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Forecast data retrieved successfully",
                "data": forecast_list,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="weather-station")
    def fetch_weather_station(self, request, pk=None):
        url = f"https://api.weather.com/v2/pws/observations/current?stationId={station_id}&format=json&units=m&apiKey={api_key}"

        try:
            response = requests.get(url)

            if response.status_code != 200:
                return Response({
                    "status": status.HTTP_204_NO_CONTENT,
                    "message": f"Error fetching weather data",
                }, status=status.HTTP_204_NO_CONTENT)
            
            data = response.json()
            obs = data['observations'][0]
            
            weather_data = {
                "station_id": obs['stationID'],
                "temperature": obs['metric']['temp'],
                "humidity": obs['humidity'],
                "wind_speed": obs['metric']['windSpeed'],
                "pressure": obs['metric']['pressure'],
                "precip_rate": obs['metric']['precipRate'],
                "latitude": obs['lat'],
                "longitude": obs['lon'],
                "last_update": obs['obsTimeLocal']
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Weather data retrieved successfully",
                "data": weather_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)