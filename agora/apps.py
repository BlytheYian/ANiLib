from django.apps import AppConfig


class AgoraConfig(AppConfig):
    name = 'agora'

    def ready(self):
        from . import signals  # noqa: F401
