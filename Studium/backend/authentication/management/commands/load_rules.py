from django.core.management.base import BaseCommand
from rules.models import Rules
import json


class Command(BaseCommand):
    help = "Загружает фикстуры Rules, избегая дублирования"

    def handle(self, *args, **kwargs):
        with open("rules/fixtures/rules_fixture.json", encoding="utf-8") as f:
            data = json.load(f)
            for entry in data:
                obj, created = Rules.objects.update_or_create(
                    name=entry["fields"]["name"],
                    defaults={"path": entry["fields"]["path"], 
                              "type": entry["fields"]["type"]}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Добавлен {obj.path}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Обновлен {obj.path}"))
