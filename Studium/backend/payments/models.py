from django.db import models
from authentication.models import CustomUser
from ready_tasks.models import ReadyTask
from django.utils import timezone
from datetime import timedelta
from django.db import transaction as db_transaction


class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="wallet")

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    frozen = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def total(self):
        return self.balance + self.frozen


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В исполнении'),
        ('frozen', 'Заморожены'),
        ('paid', 'Исполнена'),
        ('canceled', 'Отменен'),
        ('failed', 'Ошибка'),
    ]

    RECEIPT_STATUS_CHOICES = [
        ('not_required', 'Чек не нужен'),
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлен'),
        ('failed', 'Ошибка отправки'),
    ]

    external_id = models.TextField(null=False, blank=False, default='studium_none')

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    type = models.CharField(max_length=20, choices=[
        ("deposit", "Пополнение"),
        ("withdraw", "Вывод"),
        ("purchase_ready_task", "Покупка работы"),
        ("purchase_slots", "Покупка слотов"),
        ("refund", "Возврат"),
        ("reward", "Начисление за продажу"),
    ])

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Статус транзакции")
    created_at = models.DateTimeField(auto_now_add=True)

    receipt_status = models.CharField(
        max_length=20,
        choices=RECEIPT_STATUS_CHOICES,
        default='not_required',
        help_text="Статус отправки чека"
    )

    def is_expired(self, hours=1):
        return (timezone.now() - self.created_at) > timedelta(hours=hours) and self.status == 'pending'

    def mark_as_paid(self, save=True):
        if self.status == 'pending':
            self.status = 'paid'
            with db_transaction.atomic():
                if self.type == "deposit":
                    self.wallet.balance = (self.wallet.balance or 0) + self.amount
                    self.wallet.save(update_fields=["balance"])
                if save:
                    self.save()
            return True
        return False

    def mark_as_canceled(self, save=True):
        if self.status == 'pending':
            self.status = 'canceled'
            if save:
                self.save()
            return True
        return False

    def mark_as_failed(self, save=True):
        if self.status == 'pending':
            self.status = 'failed'
            if save:
                self.save()
            return True
        return False


class FrozenFunds(models.Model):
    STATUS_CHOICES = [
        ('frozen', 'Заморожено'),
        ('released', 'Разблокировано и переведено'),
        ('cancelled', 'Отменено, возвращено отправителю'),
        ('disputed', 'Спор, временно заморожено'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions_funds")
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE,
                                    related_name="frozen_funds")

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    release_at = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='frozen')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Замороженные средства"
        verbose_name_plural = "Замороженные средства"


class PurchasedReadyTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании оплаты'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменен'),
        ('refunded', 'Возвращен'),
    ]

    buyer_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE,
                                          related_name="buyer_purchases", help_text="Транзакция покупки для покупателя")

    seller_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE,
                                           related_name="seller_purchases", help_text="Транзакция покупки для продавца")

    refund_buyer_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL,
                                                 null=True, blank=True, related_name="buyer_refund",
                                                 help_text="Транзакция возврата, если была")

    refund_seller_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL,
                                                  null=True, blank=True, related_name="seller_refund",
                                                  help_text="Транзакция возврата, если была")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Статус покупки")

    ready_task = models.ForeignKey(ReadyTask, on_delete=models.CASCADE,
                                   related_name="purchases", help_text="Приобретённая работа")

    payment_amount = models.DecimalField(max_digits=12, decimal_places=2,
                                         help_text="Сумма которую заплатил покупатель")

    commission = models.DecimalField(max_digits=12, decimal_places=2,
                                     default=0, help_text="Сумма удержанной комиссии")

    net_amount = models.DecimalField(max_digits=12, decimal_places=2,
                                     default=0, help_text="Чистая сумма, зачисляемая продавцу")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Время создания записи покупки")

    is_gift = models.BooleanField(default=False,
                                  help_text="Товар остается у пользователя как подарок при возврате")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Покупка работы"
        verbose_name_plural = "Покупки работ"

    def mark_as_paid(self):
        self.status = 'paid'
        self.save(update_fields=["status"])

    def mark_as_canceled(self):
        self.status = 'canceled'
        self.save(update_fields=["status"])

    def mark_as_refunded(self):
        self.status = 'refunded'
        self.save(update_fields=["status"])


class SlotPackage(models.Model):
    slots_count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slots_count"]


class SlotsPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании оплаты'),
        ('paid', 'Оплачен'),
        ('canceled', 'Отменен'),
        ('refunded', 'Возвращен'),
    ]

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE,
                                    related_name="purchases_slots", help_text="Транзакция покупки")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Статус покупки")

    count_slots = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True, help_text="Время создания записи покупки")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Покупка слотов"
        verbose_name_plural = "Покупки слотов"


class Bank(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название банка")
    bank_id = models.CharField(max_length=50, unique=True, verbose_name="Идентификатор банка в Jump Finance")

    def __str__(self):
        return f"{self.name} ({self.bank_id})"

    class Meta:
        verbose_name = "Банк"
        verbose_name_plural = "Банки"
        ordering = ["name"]
