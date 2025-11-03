from django.db import models
from django.utils import timezone
from payments.models import PurchasedReadyTask


class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('requested', 'Запрошен'),
        ('processing', 'В обработке'),
        ('approved', 'Одобрен'),
        ('completed', 'Выполнен'),
        ('rejected', 'Отклонен'),
        ('failed', 'Ошибка'),
    ]

    purchase = models.ForeignKey(
        PurchasedReadyTask,
        on_delete=models.CASCADE,
        related_name="refunds"
    )

    status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='requested'
    )

    reason = models.TextField(max_length=1000)

    contact_info = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Контактные данные для связи (email, телефон, Telegram и т.д.)"
    )

    admin_comment = models.TextField(max_length=1000, blank=True, null=True)

    keep_product = models.BooleanField(
        default=False,
        help_text="Средства возвращаются, но товар остаётся у пользователя"
    )

    is_admin_created = models.BooleanField(default=False, help_text="Оформил ли заявку админ")

    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    processed_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="processed_refunds"
    )

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"Refund #{self.id} for Purchase #{self.purchase.id}"

    def mark_as_processing(self):
        self.status = 'processing'
        self.save(update_fields=["status"])

    def mark_as_approved(self, user=None):
        self.status = 'approved'
        self.processed_at = timezone.now()
        if user:
            self.processed_by = user
        self.save(update_fields=["status", "processed_at", "processed_by"])

    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def mark_as_rejected(self, user=None, comment=None):
        self.status = 'rejected'
        self.processed_at = timezone.now()
        if user:
            self.processed_by = user
        if comment:
            self.admin_comment = comment
        self.save(update_fields=["status", "processed_at", "processed_by", "admin_comment"])

    def mark_as_failed(self):
        self.status = 'failed'
        self.save(update_fields=["status"])

    def get_contact_display(self):
        if self.contact_info:
            return self.contact_info
        elif self.purchase.buyer:
            return f"{self.purchase.buyer.email} (из профиля)"
        return "Не указано"


class Files(models.Model):
    refund = models.ForeignKey(Refund, related_name='files', on_delete=models.CASCADE)
    name = models.TextField()
    path = models.TextField(max_length=1000, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Файл для комментария #{self.refund.id}"

    class Meta:
        verbose_name = "Файл запроса на возврат"
        verbose_name_plural = "Файлы запросов на возврат"
