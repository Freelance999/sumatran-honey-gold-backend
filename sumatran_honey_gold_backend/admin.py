from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Client, LiveHarvest, HoneyBatch, HoneyBottle

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'date_joined')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'logo', 'created_at', 'updated_at')

class LiveHarvestAdmin(admin.ModelAdmin):
    list_display = ('client', 'youtube_video_id', 'start_time', 'end_time', 'latitude', 'longitude', 'status', 'created_at', 'updated_at')

class HoneyBatchAdmin(admin.ModelAdmin):
    list_display = ('live_harvest', 'brand', 'quantity', 'created_at', 'updated_at')

class HoneyBottleAdmin(admin.ModelAdmin):
    list_display = ('honey_batch', 'qr_code', 'serial_number', 'created_at', 'updated_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(LiveHarvest, LiveHarvestAdmin)
admin.site.register(HoneyBatch, HoneyBatchAdmin)
admin.site.register(HoneyBottle, HoneyBottleAdmin)