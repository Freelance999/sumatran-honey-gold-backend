from rest_framework import serializers
from django.contrib.auth import get_user_model
# from .models import 

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    
    class Meta(object):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_active', 'date_joined']