from django.core.management.base import BaseCommand
from payments.models import SlotPackage
import json
import os


class Command(BaseCommand):
    help = "Загружает/обновляет SlotPackage из fixtures при старте контейнера"

    def handle(self, *args, **kwargs):
        fixture_candidates = [
            "payments/fixtures/slot_packages.json",
            os.path.join("backend", "payments", "fixtures", "slot_packages.json"),
        ]

        fixture_path = next((p for p in fixture_candidates if os.path.exists(p)), None)
        if not fixture_path:
            self.stderr.write(self.style.ERROR("Не найден файл fixtures slot_packages.json"))
            return

        try:
            with open(fixture_path, encoding="utf-8") as f:
                data = json.load(f)
                for entry in data:
                    fields = entry.get("fields", {})
                    slots_count = fields.get("slots_count")
                    if slots_count is None:
                        continue
                    defaults = {
                        "price": fields.get("price"),
                        "old_price": fields.get("old_price"),
                        "description": fields.get("description", ""),
                        "is_active": fields.get("is_active", True),
                    }
                    obj, created = SlotPackage.objects.update_or_create(
                        slots_count=slots_count,
                        defaults=defaults,
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Добавлен пакет {obj.slots_count} слотов"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Обновлен пакет {obj.slots_count} слотов"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка загрузки фикстуры {fixture_path}: {e}"))
