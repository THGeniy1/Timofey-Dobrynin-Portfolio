from django.apps import AppConfig


class TestAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ready_tasks'

    def ready(self):
        import ready_tasks.signals
