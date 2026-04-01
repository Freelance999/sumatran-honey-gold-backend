import os
import binascii
from django.db import models
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    def __str__(self):
        return self.username
    
class UserToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_tokens', on_delete=models.CASCADE)
    last_used = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        if not self.expires_at:
            days = getattr(settings, "ACCESS_TOKEN_EXPIRY")
            self.expires_at = timezone.now() + timedelta(days=days)
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def is_expired(self):
        return timezone.now() > self.expires_at if self.expires_at else False
    
    class Meta:
        pass

class RefreshToken(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='refresh_tokens', on_delete=models.CASCADE)
    is_revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = binascii.hexlify(os.urandom(32)).decode()
        if not self.expires_at:
            days = getattr(settings, "REFRESH_TOKEN_EXPIRY")
            self.expires_at = timezone.now() + timedelta(days=days)
        return super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at
    
class PasswordResetToken(models.Model):
    custom_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='password_reset_tokens', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = binascii.hexlify(os.urandom(32)).decode()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        return super().save(*args, **kwargs)

    def is_valid(self):
        return (not self.is_used) and timezone.now() <= self.expires_at

class Client(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True)
    logo = models.ImageField(upload_to='images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Block(models.Model):
    code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class LiveHarvest(models.Model):
    client = models.ForeignKey(Client, related_name='live_harvests', on_delete=models.CASCADE, null=True, blank=True)
    block = models.ForeignKey(Block, related_name='live_harvests', on_delete=models.SET_NULL, null=True, blank=True)
    youtube_video_id = models.CharField(max_length=100, null=True, blank=True)
    youtube_stream_id = models.CharField(max_length=100, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    weather_temperature = models.FloatField(null=True, blank=True)
    weather_humidity = models.FloatField(null=True, blank=True)
    weather_wind_speed = models.FloatField(null=True, blank=True)
    weather_uv = models.FloatField(null=True, blank=True)
    weather_rain = models.FloatField(null=True, blank=True)
    harvester_name = models.CharField(max_length=100, null=True, blank=True)
    cameraman = models.CharField(max_length=100, null=True, blank=True)
    water_prediction = models.FloatField(null=True, blank=True)
    selfie_photo = models.ImageField(upload_to='images/selfie/', null=True, blank=True)
    area_photo = models.ImageField(upload_to='images/area/', null=True, blank=True)
    sky_photo = models.ImageField(upload_to='images/sky/', null=True, blank=True)
    water_prediction_photo = models.ImageField(upload_to='images/water_prediction/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class HoneyBatch(models.Model):
    live_harvest = models.ForeignKey(LiveHarvest, related_name='honey_batches', on_delete=models.CASCADE, null=True, blank=True)
    batch_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} - {self.quantity}"
    
class HoneyBottle(models.Model):
    honey_batch = models.ForeignKey(HoneyBatch, related_name='honey_bottles', on_delete=models.CASCADE)
    qr_code = models.ImageField(upload_to='images/', null=True, blank=True)
    serial_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.honey_batch} - {self.serial_number}"

class Certificate(models.Model):
    honey_batch = models.ForeignKey(HoneyBatch, related_name='certificates', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    file = models.FileField(upload_to='files/', null=True, blank=True)
    date = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.honey_batch} - {self.title}"
    
class WeatherObservation(models.Model):
    station_id = models.CharField(max_length=50, null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    precip_rate = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    observed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["observed_at"]),
            models.Index(fields=["station_id", "observed_at"]),
        ]

    def __str__(self):
        return f"Weather at {self.observed_at} - Temp: {self.temperature}°C"
    
class Setting(models.Model):
    key = models.CharField(max_length=255,unique=True, null=True, blank=True)
    value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}"