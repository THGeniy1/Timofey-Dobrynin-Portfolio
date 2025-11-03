from django.contrib import admin

from .models import Wallet, Transaction, FrozenFunds, PurchasedReadyTask, SlotsPurchase, SlotPackage, Bank


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "bank_id")
    list_display_links = ("id", "name")
    search_fields = ("name", "bank_id")
    ordering = ("name",)

    fieldsets = (
        (None, {
            'fields': ('name', 'bank_id')
        }),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "user_email", "balance", "frozen", "total_amount")
    search_fields = ("user__email", "user__name")
    list_select_related = ("user",)

    def user_email(self, obj):
        return obj.user.email if obj.user else ""

    user_email.short_description = "Email пользователя"

    def total_amount(self, obj):
        return obj.total()

    total_amount.short_description = "Итого"


class PurchasedReadyTaskInline(admin.TabularInline):
    model = PurchasedReadyTask
    fk_name = "buyer_transaction"
    extra = 0
    fields = ("ready_task", "status", "created_at", "buyer_transaction", "seller_transaction")
    readonly_fields = ("created_at",)


class SlotsPurchaseInline(admin.TabularInline):
    model = SlotsPurchase
    extra = 0
    fields = ("count_slots", "status", "created_at")
    readonly_fields = ("created_at",)


class FrozenFundsInline(admin.TabularInline):
    model = FrozenFunds
    extra = 0
    fields = ("wallet", "amount", "status", "release_at", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "external_id",
        "wallet",
        "user_email",
        "amount",
        "type",
        "status",
        "receipt_status",
        "created_at",
        "is_expired_flag",
    )
    list_filter = (
        "external_id",
        "type",
        "status",
        "receipt_status",
        "created_at"
    )
    search_fields = ("wallet__user__email",)
    list_select_related = ("wallet", "wallet__user")
    inlines = [PurchasedReadyTaskInline, SlotsPurchaseInline, FrozenFundsInline]

    def user_email(self, obj):
        return obj.wallet.user.email if obj.wallet and obj.wallet.user else ""
    user_email.short_description = "Email пользователя"

    def is_expired_flag(self, obj):
        return obj.is_expired()
    is_expired_flag.boolean = True
    is_expired_flag.short_description = "Просрочена"


@admin.register(FrozenFunds)
class FrozenFundsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "transaction",
        "amount",
        "status",
        "release_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "release_at")
    search_fields = ("wallet__user__email", "transaction__id")
    list_select_related = ("wallet", "wallet__user", "transaction")


@admin.register(PurchasedReadyTask)
class PurchasedReadyTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer_transaction",
        "seller_transaction",
        "refund_buyer_transaction",
        "refund_seller_transaction",
        "ready_task",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "buyer_transaction__wallet__user__email",
        "seller_transaction__wallet__user__email",
        "ready_task__title",
        "buyer_transaction__id",
        "seller_transaction__id",
    )
    list_select_related = ("buyer_transaction", "buyer_transaction__wallet", "buyer_transaction__wallet__user",
                           "seller_transaction", "seller_transaction__wallet", "seller_transaction__wallet__user",
                           "ready_task")


@admin.register(SlotsPurchase)
class SlotsPurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "transaction", "count_slots", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("transaction__wallet__user__email", "transaction__id")
    list_select_related = ("transaction", "transaction__wallet", "transaction__wallet__user")


@admin.register(SlotPackage)
class SlotPackageAdmin(admin.ModelAdmin):
    list_display = ("id", "slots_count", "price", "old_price", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("description",)
    ordering = ("slots_count",)
    list_editable = ("is_active",)