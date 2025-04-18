from django.apps import AppConfig


class PagesConfig(AppConfig):
    name = "pages"

    def ready(self):
        from .activity_registry import register_activity_models
        register_activity_models()
