from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'company', 'role', 'is_superuser', 'is_staff', 'is_active', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('company', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('company', 'role')}),
    )