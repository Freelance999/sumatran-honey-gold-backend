from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, LiveHarvest, HoneyBatch, HoneyBottle, Certificate, WeatherObservation, Block, Setting, Role, RawStock, Bottling, Brand, Inventory, School, Teacher, TeacherSchool, UserDocument, MentorPersonalOrder, DistributionMission

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta(object):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'role', 'phone_number', 'date_joined']

class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = ['id', 'name', 'color', 'logo', 'created_at', 'updated_at']

class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = ['id', 'code', 'name', 'created_at', 'updated_at']

class LiveHarvestSerializer(serializers.ModelSerializer):
    block = BlockSerializer(read_only=True)
    block_id = serializers.PrimaryKeyRelatedField(queryset=Block.objects.all(), source='block', write_only=True)

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

class SettingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Setting
        fields = ['id', 'key', 'value', 'created_at', 'updated_at']

class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ['id', 'name', 'id_role', 'created_at', 'updated_at']

class RawStockSerializer(serializers.ModelSerializer):

    class Meta:
        model = RawStock
        fields = ['id', 'live_harvest', 'live_harvest_id', 'weight_kg', 'remaining_kg', 'status', 'created_at', 'updated_at']


class BottlingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bottling
        fields = ['id', 'raw_stock', 'raw_stock_id', 'bottle_size_ml', 'quantity', 'used_kg', 'created_at', 'updated_at']

class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo', 'is_active', 'created_at', 'updated_at']

class InventorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Inventory
        fields = ['id', 'brand', 'brand_id', 'bottle_size_ml', 'stock', 'created_at', 'updated_at']


class SchoolSerializer(serializers.ModelSerializer):

    class Meta:
        model = School
        fields = ['id', 'name', 'address', 'created_at', 'updated_at']


class TeacherSchoolSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), source='school', write_only=True)

    class Meta:
        model = TeacherSchool
        fields = ['id', 'teacher', 'teacher_id', 'school', 'school_id', 'created_at', 'updated_at']


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    mentor = UserSerializer(read_only=True)
    school = SchoolSerializer(many=True, read_only=True)
    school_ids = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), source='school', many=True, write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'user_id', 'mentor', 'mentor_id', 'school', 'school_ids', 'customer_count', 'omzet', 'created_at', 'updated_at']


class UserDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserDocument
        fields = ['id', 'user', 'user_id', 'url', 'type', 'created_at', 'updated_at']


class MentorPersonalOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = MentorPersonalOrder
        fields = ['id', 'mentor', 'mentor_id', 'teacher', 'teacher_id', 'product_name', 'weight', 'quantity', 'unit_price', 'line_total', 'buyer_type', 'school', 'school_id', 'buyer_name', 'buyer_reference', 'created_at', 'updated_at']


class DistributionMissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistributionMission
        fields = ['id', 'user', 'user_id', 'year', 'target_quantity', 'created_at', 'updated_at']
