from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Client, LiveHarvest, HoneyBatch, HoneyBottle, Certificate, WeatherObservation, Block, Setting, Role

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'role', 'date_joined')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'logo', 'created_at', 'updated_at')

class LiveHarvestAdmin(admin.ModelAdmin):
    list_display = ('client', 'block', 'youtube_video_id', 'youtube_stream_id', 'start_time', 'end_time', 'latitude', 'longitude', 'status', 'weather_temperature', 'weather_humidity', 'weather_wind_speed', 'weather_uv', 'weather_rain', 'harvester_name', 'cameraman', 'water_prediction', 'selfie_photo', 'area_photo', 'sky_photo', 'water_prediction_photo', 'created_at', 'updated_at')

class HoneyBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'live_harvest', 'brand', 'quantity', 'weight', 'status', 'created_at', 'updated_at')

class HoneyBottleAdmin(admin.ModelAdmin):
    list_display = ('honey_batch', 'qr_code', 'serial_number', 'created_at', 'updated_at')

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('honey_batch', 'title', 'description', 'file', 'date', 'created_at', 'updated_at')

class WeatherObservationAdmin(admin.ModelAdmin):
    list_display = ('station_id', 'temperature', 'humidity', 'wind_speed', 'pressure', 'precip_rate', 'latitude', 'longitude', 'observed_at', 'created_at', 'updated_at')

class BlockAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at', 'updated_at')

class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'created_at', 'updated_at')

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_role', 'created_at', 'updated_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(LiveHarvest, LiveHarvestAdmin)
admin.site.register(HoneyBatch, HoneyBatchAdmin)
admin.site.register(HoneyBottle, HoneyBottleAdmin)
admin.site.register(Certificate, CertificateAdmin)
admin.site.register(WeatherObservation, WeatherObservationAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(Role, RoleAdmin)