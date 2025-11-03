from rest_framework import serializers

from .models import Wallet, Transaction, FrozenFunds, SlotPackage, PurchasedReadyTask, SlotsPurchase


class WalletSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'frozen', 'total']

    @staticmethod
    def get_total(obj):
        return obj.total()


class TransactionSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    formatted_amount = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'external_id', 'wallet', 'created_at', 'status', 'status_display', 'amount',
                  'formatted_amount', 'type', 'type_display', 'formatted_date', 'is_expired', 'receipt_status']

    @staticmethod
    def get_formatted_amount(obj):
        return f"{obj.amount} ₽"

    @staticmethod
    def get_formatted_date(obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['is_expired'] = instance.is_expired()
        return ret


class FrozenFundsSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    transaction = TransactionSerializer(read_only=True)

    class Meta:
        model = FrozenFunds
        fields = ['id', 'wallet', 'transaction', 'amount', 'reason', 'created_at', 'release_at', 'status']


class SlotPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotPackage
        fields = ['id', 'slots_count', 'price', 'old_price', 'description', 'is_active', 'created_at', 'updated_at']


class PurchasedReadyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasedReadyTask
        fields = ['id', 'buyer_transaction', 'seller_transaction', 'refund_buyer_transaction',
                  'refund_seller_transaction', 'status', 'ready_task', 'payment_amount',
                  'commission', 'net_amount', 'created_at']


class SlotsPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotsPurchase
        fields = ['id', 'transaction', 'status', 'count_slots', 'created_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['external_id', 'wallet', 'amount', 'type', 'status', 'receipt_status']


class FrozenFundsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrozenFunds
        fields = ['wallet', 'transaction', 'amount', 'reason', 'release_at', 'status']


class PurchasedReadyTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasedReadyTask
        fields = ['buyer_transaction', 'seller_transaction', 'refund_buyer_transaction',
                  'refund_seller_transaction', 'status', 'ready_task', 'payment_amount',
                  'commission', 'net_amount']


class SlotsPurchaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotsPurchase
        fields = ['transaction', 'status', 'count_slots']
