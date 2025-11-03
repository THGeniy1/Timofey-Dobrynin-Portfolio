import logging
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.utils import timezone
from payments.models import PurchasedReadyTask, Transaction, FrozenFunds
from payments.serializers import TransactionCreateSerializer

from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException
from .models import Refund

from .serializers import RefundCreateSerializer
from .tasks import create_refund

from payments.utils import AtolService

logger = logging.getLogger(__name__)


class RefundCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RefundCreateSerializer

    @catch_and_log_exceptions
    def create(self, request, *args, **kwargs):
        print("🔹 [RefundCreateView.create] request.data:", request.data)

        data = request.data.copy()
        user = request.user
        print("🔹 [RefundCreateView.create] data (копия):", data)

        data = self._validate_values(data, user)

        email = data.pop("email", None)
        phone = data.pop("phone", None)
        print(f"🔹 [RefundCreateView.create] email={email}, phone={phone}")

        contact_parts = []
        if email:
            contact_parts.append(f"email: {email}")
        if phone:
            contact_parts.append(f"Телефон: {phone}")

        if contact_parts:
            data["contact_info"] = ", ".join(contact_parts)
        print("🔹 [RefundCreateView.create] data (после contact_info):", data)

        files_data = self._prepare_file_data(data)
        print("🔹 [RefundCreateView.create] data (после files):", files_data)

        serializer = self.get_serializer(data=data)
        print("🔹 [RefundCreateView.create] serializer initial data:", serializer.initial_data)

        if serializer.is_valid():
            print("✅ [RefundCreateView.create] serializer valid")
            task_data = {"user": user.id, 'refund_data': data} | files_data
            create_refund.delay(task_data=task_data)
            print("🚀 [RefundCreateView.create] Celery задача отправлена")
            return Response(
                {"message": "Данные приняты, идет обработка."},
                status=status.HTTP_202_ACCEPTED
            )

        raise AppException(message='Данные не прошли проверку', status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _validate_values(validated_data, user) -> dict:
        print("🔹 [_validate_values] validated_data:", validated_data, "user:", user)

        object_id = validated_data.get("object_id")
        print("🔹 [_validate_values] object_id:", object_id)

        purchased = PurchasedReadyTask.objects.filter(
            buyer_transaction__wallet__user=user,
            ready_task__id=object_id,
            status="paid",
        ).first()
        print("🔹 [_validate_values] purchased:", purchased)

        if not purchased:
            print("❌ [_validate_values] запись не найдена")
            raise ValidationError({"create_refund_validate_values": "Не найдена запись о покупке"})

        print("✅ [_validate_values] найден purchased.id:", purchased.id)
        validated_data["purchased_id"] = purchased.id
        return validated_data

    @staticmethod
    def _prepare_file_data(data):
        print("\n=== Preparing File Data ===")
        file_names = data.getlist("file_names")
        file_paths = data.getlist("file_paths")
        print(f"File names: {file_names}")
        print(f"File paths: {file_paths}")

        if len(file_names) == len(file_paths):
            result = {
                'files': [
                    {'name': name, 'path': path}
                    for name, path in zip(file_names, file_paths)
                ]
            }
            print(f"Prepared file data: {result}")
            return result
        print("No files to process")
        return {'files': []}


class RefundProcessView(APIView):
    permission_classes = [IsAdminUser]

    @catch_and_log_exceptions
    def get(self, request, refund_id):
        refund = Refund.objects.get(id=refund_id)
        action = request.data.get("action")
        comment = request.data.get("comment")

        if action == "processing":
            refund.mark_as_processing()
            return Response({"detail": "Возврат переведен в обработку"})

        if action == "approve":
            return self._approve_refund(refund, request.user)

        if action == "reject":
            refund.mark_as_rejected(user=request.user, comment=comment)
            return Response({"detail": "Возврат отклонён"})

        if action == "fail":
            refund.mark_as_failed()
            return Response({"detail": "Возврат отмечен как ошибка"})

        if action == "complete":
            refund.mark_as_completed()
            return Response({"detail": "Возврат завершён"})

        return Response({"error": "Некорректное действие"}, status=status.HTTP_400_BAD_REQUEST)

    def _approve_refund(self, refund: Refund, admin_user):
        purchase = refund.purchase

        with transaction.atomic():
            buyer_refund_txn = self._create_buyer_refund_transaction(purchase, refund.keep_product)
            self._apply_seller_deduction(purchase, purchase.net_amount)
            seller_refund_txn = self._create_seller_refund_transaction(
                purchase.seller_transaction.wallet, purchase.net_amount
            )

            self._update_purchase_after_refund(purchase, buyer_refund_txn, seller_refund_txn, refund.keep_product)
            refund.mark_as_approved(user=admin_user)

            self._create_refund_receipt(purchase, buyer_refund_txn)

        return Response({"detail": "Возврат одобрен. Средства списаны у продавца и возвращены покупателю."})

    @staticmethod
    def _create_buyer_refund_transaction(purchase: PurchasedReadyTask, keep_product: bool) -> Transaction:
        buyer_wallet = purchase.buyer_transaction.wallet
        payment_amount = purchase.payment_amount

        now = timezone.now()
        external_id = f"studium_rt_buy_reff_{buyer_wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

        transaction_data = {
            'external_id': external_id,
            'wallet': buyer_wallet.id,
            'amount': payment_amount,
            'type': 'refund',
            'status': 'pending',
            'receipt_status': 'pending' if not keep_product else None,
        }

        serializer = TransactionCreateSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)
        txn = serializer.save(wallet=buyer_wallet)

        buyer_wallet.balance = (buyer_wallet.balance or 0) + payment_amount
        buyer_wallet.save(update_fields=["balance"])
        txn.mark_as_paid()
        return txn

    @staticmethod
    def _apply_seller_deduction(purchase: PurchasedReadyTask, net_amount):
        seller_wallet = purchase.seller_transaction.wallet

        frozen_record = FrozenFunds.objects.filter(
            transaction=purchase.seller_transaction,
            status='frozen'
        ).first()

        if frozen_record:
            seller_wallet.frozen = (seller_wallet.frozen or 0) - net_amount
            if seller_wallet.frozen < 0:
                seller_wallet.balance = (seller_wallet.balance or 0) + seller_wallet.frozen
                seller_wallet.frozen = 0
            seller_wallet.save(update_fields=["balance", "frozen"])

            frozen_record.status = 'cancelled'
            frozen_record.save(update_fields=["status"])
        else:
            seller_wallet.balance = (seller_wallet.balance or 0) - net_amount
            seller_wallet.save(update_fields=["balance"])

    @staticmethod
    def _create_seller_refund_transaction(seller_wallet, net_amount) -> Transaction:
        now = timezone.now()
        external_id = f"studium_rt_sell_reff_{seller_wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

        transaction_data = {
            'external_id': external_id,
            'wallet': seller_wallet.id,
            'amount': net_amount,
            'type': 'refund',
            'status': 'paid',
        }

        serializer = TransactionCreateSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)
        return serializer.save(wallet=seller_wallet)

    @staticmethod
    def _update_purchase_after_refund(purchase: PurchasedReadyTask, buyer_txn: Transaction,
                                      seller_txn: Transaction, keep_product: bool):
        purchase.status = 'refunded'
        purchase.refund_buyer_transaction = buyer_txn
        purchase.refund_seller_transaction = None if keep_product else seller_txn
        purchase.is_gift = keep_product
        purchase.save(update_fields=[
            "status",
            "refund_buyer_transaction",
            "refund_seller_transaction",
            "is_gift",
        ])

    @staticmethod
    def _create_refund_receipt(purchase: PurchasedReadyTask, buyer_txn: Transaction):
        if purchase.is_gift:
            return

        items = [
            {
                "name": f"Возврат за работу {purchase.ready_task.id}",
                "price": float(purchase.payment_amount),
                "quantity": 1.0,
                "sum": float(purchase.payment_amount),
                "payment_method": "full_payment",
                "payment_object": "service",
                "vat": {"type": "none"},
            }
        ]

        buyer_user = purchase.buyer_transaction.wallet.user if purchase.buyer_transaction else None
        client_data = {"email": buyer_user.email} if buyer_user else {}
        seller_user = purchase.ready_task.owner

        AtolService.instance().create_refund_receipt(
            external_id=buyer_txn.external_id,
            total=float(purchase.payment_amount),
            items=items,
            client=client_data,
            supplier_user=seller_user,
        )
