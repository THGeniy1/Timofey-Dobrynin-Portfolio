from django.core.management.base import BaseCommand
from jsons.models import JsonFile
import json


class Command(BaseCommand):
    help = "Загружает фикстуры JsonFile, избегая дублирования"

    def handle(self, *args, **kwargs):
        with open("jsons/fixtures/jsonfile_fixture.json", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                obj, created = JsonFile.objects.update_or_create(
                    path=entry["fields"]["path"],
                    defaults={"name": entry["fields"]["name"]}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Добавлен {obj.path}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Обновлен {obj.path}"))
