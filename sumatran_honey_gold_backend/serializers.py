from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, LiveHarvest, HoneyBatch, HoneyBottle

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta(object):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active', 'date_joined']

class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = ['id', 'name', 'color', 'logo', 'created_at', 'updated_at']

class LiveHarvestSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiveHarvest
        fields = ['id', 'client', 'client_id', 'youtube_video_id', 'start_time', 'end_time', 'latitude', 'longitude', 'status', 'created_at', 'updated_at']

class HoneyBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = HoneyBatch
        fields = ['id', 'live_harvest', 'live_harvest_id', 'brand', 'quantity', 'created_at', 'updated_at']

class HoneyBottleSerializer(serializers.ModelSerializer):

    class Meta:
        model = HoneyBottle
        fields = ['id', 'honey_batch', 'honey_batch_id', 'qr_code', 'serial_number', 'created_at', 'updated_at']