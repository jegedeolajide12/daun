from django.apps import AppConfig
from django.contrib.auth import get_user_model

from actstream import registry

from .models import Course

user = get_user_model()

def register_activity_models():
    registry.register(user)
    registry.register(Course)