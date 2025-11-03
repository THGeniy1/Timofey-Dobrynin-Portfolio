from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AuthenticationConfig(AppConfig):
    name = 'authentication'
    verbose_name = "Authentication"

    def ready(self):
        from .client_group_settings import create_client_group

        post_migrate.connect(create_client_group, sender=self)

        import authentication.signals
