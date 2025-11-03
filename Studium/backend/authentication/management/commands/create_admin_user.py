from django.core.management.base import BaseCommand
from authentication.models import CustomUser, Staff


class Command(BaseCommand):
    help = "Создает суперпользователя AdminUser"

    def handle(self, *args, **kwargs):
        email = "admin@example.com"
        password = "admin123"

        if not CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.create_superuser(email=email, password=password, name="Super Admin")
            Staff.objects.create(user=user, role="superadmin")
            self.stdout.write(self.style.SUCCESS(f"Супер-админ {email} создан!"))
        else:
            self.stdout.write(self.style.WARNING("Супер-админ уже существует!"))
