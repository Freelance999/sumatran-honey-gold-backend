from django.urls import path
from .views import *

urlpatterns = [
    path('create-new-password', create_new_password_page, name='create-new-password'),
]