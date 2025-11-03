from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"

    def ready(self):
        from .tasks import check_withdrawals_status
        try:
            check_withdrawals_status.delay()
        except Exception as e:
            print(f"[INIT TASK ERROR] Ошибка запуска проверки выплат: {e}")
