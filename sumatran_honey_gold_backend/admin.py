from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Client, LiveHarvest, HoneyBatch, HoneyBottle, Certificate, WeatherObservation, Block, Setting, Role, RawStock, Bottling, Brand, HoneyProduct, Inventory, School, Teacher, TeacherSchool, UserDocument, MentorPersonalOrder, DistributionMission, CustomerAddress, Size, General

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active', 'role', 'phone_number', 'date_joined')

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'logo', 'created_at', 'updated_at')

class LiveHarvestAdmin(admin.ModelAdmin):
    list_display = ('client', 'block', 'youtube_video_id', 'youtube_stream_id', 'start_time', 'end_time', 'latitude', 'longitude', 'status', 'weather_temperature', 'weather_humidity', 'weather_wind_speed', 'weather_uv', 'weather_rain', 'harvester_name', 'cameraman', 'water_prediction', 'selfie_photo', 'area_photo', 'sky_photo', 'water_prediction_photo', 'created_at', 'updated_at')

class HoneyBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'live_harvest', 'brand', 'honey_product', 'quantity', 'weight', 'status', 'created_at', 'updated_at')

class HoneyProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'name', 'badge', 'bottle_size_ml', 'price', 'display_order', 'created_at', 'updated_at')
    list_filter = ('brand', 'bottle_size_ml')
    search_fields = ('name', 'badge', 'brand__name')

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

class RawStockAdmin(admin.ModelAdmin):
    list_display = ('live_harvest', 'weight_kg', 'remaining_kg', 'status', 'created_at', 'updated_at')

class BottlingAdmin(admin.ModelAdmin):
    list_display = ('raw_stock', 'bottle_size_ml', 'quantity', 'used_kg', 'created_at', 'updated_at')

class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'logo', 'is_active', 'created_at', 'updated_at')

class InventoryAdmin(admin.ModelAdmin):
    list_display = ('brand', 'bottle_size_ml', 'stock', 'created_at', 'updated_at')

class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'created_at', 'updated_at')
    search_fields = ('name', 'address')

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'mentor', 'customer_count', 'omzet', 'created_at', 'updated_at')
    list_filter = ('mentor',)
    search_fields = ('user__username', 'mentor__username')

class TeacherSchoolAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'school', 'created_at', 'updated_at')
    list_filter = ('school',)
    search_fields = ('teacher__user__username', 'school__name')

class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'url', 'created_at', 'updated_at')
    list_filter = ('type',)
    search_fields = ('user__username', 'url')

class MentorPersonalOrderAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'teacher', 'product_name', 'weight', 'quantity', 'unit_price', 'line_total', 'buyer_type', 'school', 'buyer_name', 'buyer_reference', 'created_at')
    list_filter = ('buyer_type', 'mentor', 'teacher')
    search_fields = ('product_name', 'mentor__username', 'teacher__user__username', 'buyer_name', 'buyer_reference', 'school__name')

class DistributionMissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'target_quantity', 'created_at', 'updated_at')
    list_filter = ('year', 'user')
    search_fields = ('user__username', 'user__email')

class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'source', 'created_at', 'updated_at')
    search_fields = ('name', 'address')

class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ml', 'created_at', 'updated_at')

class GeneralAdmin(admin.ModelAdmin):
    list_display = ('route', 'category', 'type', 'url', 'created_at', 'updated_at')
    search_fields = ('route', 'type')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(LiveHarvest, LiveHarvestAdmin)
admin.site.register(HoneyBatch, HoneyBatchAdmin)
admin.site.register(HoneyProduct, HoneyProductAdmin)
admin.site.register(HoneyBottle, HoneyBottleAdmin)
admin.site.register(Certificate, CertificateAdmin)
admin.site.register(WeatherObservation, WeatherObservationAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(RawStock, RawStockAdmin)
admin.site.register(Bottling, BottlingAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(TeacherSchool, TeacherSchoolAdmin)
admin.site.register(UserDocument, UserDocumentAdmin)
admin.site.register(MentorPersonalOrder, MentorPersonalOrderAdmin)
admin.site.register(DistributionMission, DistributionMissionAdmin)
admin.site.register(CustomerAddress, CustomerAddressAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(General, GeneralAdmin)
