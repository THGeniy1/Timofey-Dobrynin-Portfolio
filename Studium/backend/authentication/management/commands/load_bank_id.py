from django.core.management.base import BaseCommand
from payments.models import Bank
import json
import os


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fixture_candidates = [
            "payments/fixtures/banks.json",
            os.path.join("backend", "payments", "fixtures", "banks.json"),
        ]

        fixture_path = next((p for p in fixture_candidates if os.path.exists(p)), None)
        if not fixture_path:
            self.stderr.write(self.style.ERROR("Не найден файл fixtures banks.json"))
            return

        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    # Для вашего формата фикстуры (прямые поля, а не вложенные в "fields")
                    bank_id = entry.get("bank_id")
                    name = entry.get("name")

                    if not bank_id or not name:
                        self.stdout.write(self.style.WARNING(f"Пропущена запись с неполными данными: {entry}"))
                        continue

                    obj, created = Bank.objects.update_or_create(
                        bank_id=bank_id,
                        defaults={"name": name},
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Добавлен банк {name} ({bank_id})"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Обновлен банк {name} ({bank_id})"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка загрузки фикстуры {fixture_path}: {e}"))