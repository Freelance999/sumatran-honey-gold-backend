from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, LiveHarvest, HoneyBatch, HoneyBottle, Certificate, WeatherObservation, Block, Setting, Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta(object):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'role', 'date_joined']

class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = ['id', 'name', 'color', 'logo', 'created_at', 'updated_at']

class LiveHarvestSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiveHarvest
        fields = ['id', 'client', 'client_id', 'block', 'block_id', 'youtube_video_id', 'youtube_stream_id', 'start_time', 'end_time', 'latitude', 'longitude', 'status', 'weather_temperature', 'weather_humidity', 'weather_wind_speed', 'weather_uv', 'weather_rain', 'harvester_name', 'cameraman', 'water_prediction', 'selfie_photo', 'area_photo', 'sky_photo', 'water_prediction_photo', 'created_at', 'updated_at']

class HoneyBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = HoneyBatch
        fields = ['id', 'live_harvest', 'live_harvest_id', 'batch_id', 'brand', 'quantity', 'weight', 'status', 'created_at', 'updated_at']

class HoneyBottleSerializer(serializers.ModelSerializer):

    class Meta:
        model = HoneyBottle
        fields = ['id', 'honey_batch', 'honey_batch_id', 'qr_code', 'serial_number', 'created_at', 'updated_at']

class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Certificate
        fields = ['id', 'honey_batch', 'honey_batch_id', 'title', 'description', 'file', 'date', 'created_at', 'updated_at']

class WeatherObservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeatherObservation
        fields = ['id', 'station_id', 'temperature', 'humidity', 'wind_speed', 'pressure', 'precip_rate', 'latitude', 'longitude', 'observed_at', 'created_at', 'updated_at']

class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = ['id', 'code', 'name', 'created_at', 'updated_at']

class SettingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'created_at', 'updated_at']

class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ['id', 'name', 'id_role', 'created_at', 'updated_at']