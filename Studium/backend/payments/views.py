import logging
import requests
from decimal import Decimal

from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework import status

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta

from ready_tasks.models import ReadyTask
from studium_backend.decorators import catch_and_log_exceptions
from studium_backend.exceptions import AppException
from studium_backend.utils import send_telegram_message

from .serializers import (
    TransactionSerializer, TransactionCreateSerializer,
    FrozenFundsCreateSerializer, PurchasedReadyTaskCreateSerializer,
    SlotsPurchaseCreateSerializer, SlotPackageSerializer
)
from .models import SlotPackage, Transaction, Wallet, PurchasedReadyTask, Bank

from django.db import transaction as db_transaction

from .utils import TinkoffAPI, AtolService

logger = logging.getLogger(__name__)


class BalanceTopUpView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    tApi = TinkoffAPI()

    @catch_and_log_exceptions
    def post(self, request):
        print(f"🟢 POST запрос на пополнение баланса от пользователя: {request.user}")
        print(f"📦 Данные запроса: {request.data}")

        user = request.user
        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        amount = request.data.get('amount')

        if not amount or int(amount) <= 0:
            raise AppException(message='Указана некорректная сумма', status_code=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        external_id = f"studium_up_{user.wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

        payment_data = {
            'external_id': external_id,
            'wallet': user.wallet.id,
            'amount': amount,
            'type': 'deposit',
            'status': 'pending',
        }

        serializer = TransactionCreateSerializer(data=payment_data)
        print(f"📋 Данные для сериализации: {payment_data}")

        serializer.is_valid(raise_exception=True)
        print("✅ Данные валидны")

        purchase = serializer.save(wallet=user.wallet)
        print(f"📝 Создана транзакция: ID={purchase.id}, статус={purchase.status}")

        try:
            print("🔄 Инициализация платежа в Tinkoff...")
            payment_url = self._init_tinkoff_payment(purchase, user.email)
            print(f"✅ Платеж инициализирован, URL: {payment_url}")
        except Exception as e:
            print(f"🔴 Ошибка при инициализации платежа: {str(e)}")
            purchase.status = 'failed'
            purchase.save()
            print(f"📝 Статус транзакции изменен на 'failed'")
            raise ValidationError({"payment": str(e)})

        response_data = {
            "payment_url": payment_url
        }

        print(f"✅ Успешный ответ, статус: {status.HTTP_201_CREATED}")
        return Response(response_data, status=status.HTTP_201_CREATED)

    def _init_tinkoff_payment(self, purchase, user_email):
        """Инициализирует платеж в Tinkoff и возвращает PaymentURL."""
        print(f"🔧 Начало инициализации платежа для транзакции ID: {purchase.id}")

        payload = {
            "TerminalKey": settings.TINKOFF_TERMINAL_KEY,
            "Amount": int(purchase.amount * 100),  
            "OrderId": str(purchase.id),  
            "Description": "Пополнение счета на сайте",
            # "Receipt": {
            #     "Email": user_email,  # email покупателя
            #     "Taxation": "usn_income",  # твоя система налогообложения
            #     "Items": [
            #         {
            #             "Name": "Пополнение кошелька на сайте",
            #             "Price": int(purchase.amount * 100),  # цена за единицу (в копейках)
            #             "Quantity": 1.0,  # количество можно float
            #             "Amount": int(purchase.amount * 100),  # Price * Quantity
            #             "PaymentMethod": "advance",  # способ оплаты
            #             "PaymentObject": "payment",  # объект расчета
            #             "Tax": "none",  # ставка НДС
            #         }
            #     ]
            # },
            "NotificationURL": f"{settings.BASE_URL}/api/payments/tinkoff_notify/",
        }

        print(f"📤 Payload для Tinkoff API: {payload}")

        response = self.tApi.request("Init", payload)
        print(f"📥 Ответ от Tinkoff API: {response}")

        if not response.get("Success"):
            error_message = response.get("Message", "Payment initialization failed")
            raise ValidationError({"tinkoff_payment": str(error_message)})

        payment_url = response["PaymentURL"]
        print(f"🔗 Получен PaymentURL: {payment_url}")

        return payment_url


@method_decorator(csrf_exempt, name="dispatch")
class TinkoffNotificationView(APIView):
    parser_classes = [JSONParser]
    tApi = TinkoffAPI()

    @catch_and_log_exceptions
    def post(self, request):
        data = request.data
        logger.info("🔔 Получено уведомление от Tinkoff: %s", data)

        try:
            logger.debug("🔍 Проверка обязательных полей уведомления...")
            self._validate_notification(data)
            logger.debug("✅ Проверка обязательных полей пройдена")

            logger.debug("🔐 Проверка подписи и поиск транзакции...")
            purchase = self._verify_notification(data)

            if not purchase:
                logger.warning("⚠ Транзакция не найдена или не прошла проверку — уведомление проигнорировано.")
                return Response({"status": "ignored"}, status=200)

            logger.info("✅ Транзакция найдена: id=%s, статус=%s, сумма=%s",
                        purchase.id, purchase.status, purchase.amount)

            logger.debug("♻ Обновление статуса платежа...")
            self._update_payment_status(purchase, data)
            logger.info("✅ Статус платежа обновлён")

            self.tApi.confirm_payment(payment_id=data.get("PaymentId"))

        except Exception as e:
            logger.exception("🛑 Ошибка при обработке уведомления: %s", e)
            logger.warning("🚫 Попытка отмены платежа через Tinkoff API...")

            try:
                self._cancel_payment(data)
                logger.info("↩ Платёж отменён после ошибки обработки")
            except Exception as cancel_error:
                logger.exception("⚠ Ошибка при отмене платежа: %s", cancel_error)

    @staticmethod
    def _validate_notification(data: dict):
        required_fields = [
            "TerminalKey", "OrderId", "Success", "Status",
            "PaymentId", "ErrorCode", "Amount", "Token"
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.error("❗ Отсутствуют обязательные поля: %s", missing)
            raise ValidationError({
                "tinkoff_field_validation": {
                    field: "Отсутствует поле" for field in missing
                }
            })

    def _verify_notification(self, data: dict):
        if data.get("TerminalKey") != settings.TINKOFF_TERMINAL_KEY:
            logger.warning("❌ Неверный TerminalKey в уведомлении")
            return None

        if not self.tApi.validate_token(data):
            logger.warning("❌ Проверка подписи не пройдена")
            return None

        purchase = Transaction.objects.filter(id=data.get('OrderId')).first()
        if not purchase:
            logger.warning("❌ Транзакция с id=%s не найдена", data.get('OrderId'))
            return None

        expected_amount = float(purchase.amount * 100)
        actual_amount = float(data["Amount"])
        logger.debug("🔎 Сверка сумм: ожидали=%s, пришло=%s", expected_amount, actual_amount)
        if expected_amount != actual_amount:
            logger.warning("❌ Суммы не совпали (ожидали=%s, пришло=%s)", expected_amount, actual_amount)
            return None

        return purchase

    def _update_payment_status(self, purchase: Transaction, data: dict):
        status_map = {
            "CONFIRMED": "paid",
            "REVERSED": "canceled",
            "REJECTED": "canceled",
            "REFUNDED": "canceled",
            "CANCELED": "canceled",
        }

        payment_status = data.get("Status", "")
        success = data.get("Success", "")
        error_code = data.get("ErrorCode", "0")
        logger.debug("📡 Статус от Tinkoff: status=%s, success=%s, errorCode=%s",
                     payment_status, success, error_code)
        is_expired = purchase.is_expired()
        logger.debug("⏱️ Транзакция просрочена: %s", is_expired)

        is_final_failure = (
                error_code != "0"
                or is_expired
                or payment_status in ["REJECTED", "CANCELED"]
        )

        if is_final_failure:
            logger.warning("🧨 Финальная ошибка/отмена, инициируем отмену платежа...")
            self._cancel_payment(data)
            logger.info("🛑 Платёж отменён")
            return

        mapped_status = status_map.get(payment_status, purchase.status)
        if mapped_status and mapped_status != purchase.status:
            logger.debug("🔁 Изменение статуса: %s -> %s", purchase.status, mapped_status)
            if payment_status == "CONFIRMED" and success:
                if purchase.status != "pending":
                    logger.warning("⚠️ Транзакция не в статусе pending при CONFIRMED — отменяем платеж")
                    self._cancel_payment(data)
                    return

                logger.info("✅ Отмечаем транзакцию как оплаченную")
                purchase.mark_as_paid()
                if purchase.receipt_status == 'pending':
                    purchase.receipt_status = 'sent'
                    purchase.save(update_fields=["receipt_status"])
                    logger.info("📄 Чек отмечен как отправленный (транзакция %s)", purchase.id)
                return

            elif payment_status == "REFUNDED" and success:
                if purchase.status == "paid":
                    with db_transaction.atomic():
                        wallet = purchase.wallet
                        old_balance = wallet.balance
                        wallet.balance = (wallet.balance or 0) - purchase.amount
                        wallet.save(update_fields=["balance"])
                        purchase.status = "canceled"
                        if purchase.receipt_status == 'pending':
                            purchase.receipt_status = 'sent'
                        purchase.save(update_fields=["status", "receipt_status"])

                    logger.info("💳 Баланс изменён: %s → %s; транзакция %s отменена",
                                old_balance, wallet.balance, purchase.id)
                else:
                    purchase.mark_as_canceled()
                    logger.info("🚫 Транзакция %s помечена как отменённая", purchase.id)

            elif payment_status == "CANCELED":
                logger.info("🚫 Отмечаем транзакцию как отменённую")
                purchase.mark_as_canceled()
        else:
            logger.debug("ℹ️ Статус не изменился, действий не требуется")

    def _cancel_payment(self, data: dict):
        payment_id = data.get("PaymentId")
        order_id = data.get("order_id")

        if not payment_id:
            logger.error("❗ Не указан payment_id для отмены")
            raise ValidationError({"tinkoff_cancel_payment": "Не найден payment_id для отмены"})

        logger.info("↩️ Отправка запроса на отмену платежа (payment_id=%s)", payment_id)
        response = self.tApi.cancel_payment(payment_id)
        logger.debug("📥 Ответ на отмену платежа: %s", response)

        if response.get("Success"):
            purchase_model = Transaction.objects.filter(id=order_id).first()
            if purchase_model:
                purchase_model.mark_as_canceled()
                logger.info("✅ Транзакция %s помечена как отменённая", purchase_model.id)
            return True

        error_message = response.get("Message", "Unknown error")
        error_code = response.get("ErrorCode", "")
        logger.error("❌ Не удалось отменить платёж: %s (код %s)", error_message, error_code)
        raise ValidationError({
            "tinkoff_cancel_payment": f"Не удалось отменить платеж: {error_message} (Код ошибки: {error_code})"
        })


class PurchaseReadyTask(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def post(self, request):
        print("▶️ Начало покупки")
        user = request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        wallet, ready_task = self._validate_data(request)

        print(f"✅ Проверка: работа {ready_task.id} найдена, цена {ready_task.price}, баланс {wallet.balance}")
        self._check_already_purchased(user, ready_task)

        amount: Decimal = Decimal(ready_task.price)
        commission: Decimal = (amount * Decimal("0.20")).quantize(Decimal("0.01"))
        net_amount: Decimal = amount - commission

        with transaction.atomic():
            buyer_transaction = self._create_purchase_transaction(wallet, ready_task)
            print(f"💰 Транзакция {buyer_transaction.id} создана, сумма {buyer_transaction.amount}")

            seller_transaction = self._freeze_seller_funds(net_amount=net_amount, ready_task=ready_task)
            print(f"💰 Транзакция {seller_transaction.id} создана, сумма {seller_transaction.amount}")

            purchase = self._create_purchase_record(
                buyer_transaction=buyer_transaction,
                seller_transaction=seller_transaction,
                ready_task=ready_task,
                amount=amount,
                net_amount=net_amount,
                commission=commission
            )
            print(f"📦 Покупка {purchase.id} создана, работа {ready_task.id}")

            client_data = {
                "email": request.user.email,
            }

            items = [
                {
                    "name": f"Покупка работы {ready_task.id}",
                    "price": float(ready_task.price),
                    "quantity": 1.0,
                    "sum": float(ready_task.price),
                    "payment_method": "full_payment",
                    "payment_object": "service",
                    "vat": {"type": "none"},
                }
            ]

            AtolService.instance().create_agent_receipt(
                external_id=buyer_transaction.external_id,
                total=float(ready_task.price),
                items=items,
                supplier_user=ready_task.owner,
                client=client_data,
            )

        print("🎉 Покупка завершена успешно")
        return Response(
            {"status": "success", "message": "Оплата успешно завершена"},
            status=status.HTTP_200_OK
        )

    @staticmethod
    def _validate_data(request):
        user = request.user
        task_id = request.data.get("task_id")

        if not task_id:
            raise ValidationError({"purchase_ready_task_validate_data": 'Не передан ключ работы'})

        ready_task = ReadyTask.objects.filter(id=task_id).first()
        if not ready_task:
            raise ValidationError({"purchase_ready_task_validate_data": 'Не найдена работа по переданному ключу'})

        wallet = user.wallet
        if wallet.balance < ready_task.price:
            raise AppException(message='Недостаточно средств для покупки', status_code=status.HTTP_400_BAD_REQUEST)

        return wallet, ready_task

    @staticmethod
    def _check_already_purchased(user, ready_task: ReadyTask):
        print(f"🔍 Проверка: покупал ли пользователь {user.id} работу {ready_task.id}")
        exists = PurchasedReadyTask.objects.filter(
            buyer_transaction__wallet__user=user,
            ready_task=ready_task,
            status="paid"
        ).exists()

        if exists:
            raise AppException(message='Эта работа уже куплена', status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _create_purchase_transaction(wallet: Wallet, ready_task: ReadyTask):
        print(f"💳 Создание транзакции покупки: buyer={wallet.user.id}, сумма={ready_task.price}")

        now = timezone.now()
        external_id = f"studium_rt_buy_{wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

        transaction_data = {
            'external_id': external_id,
            'wallet': wallet.id,
            'amount': ready_task.price,
            'type': 'purchase_ready_task',
            'status': 'paid',
            'receipt_status': 'pending',
        }

        serializer = TransactionCreateSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)
        buyer_transaction = serializer.save(wallet=wallet)

        wallet.balance = (wallet.balance or 0) - ready_task.price
        wallet.save(update_fields=["balance"])
        print(f"💸 Списано {ready_task.price}, новый баланс={wallet.balance}")

        print(f"✅ Транзакция {buyer_transaction.id} отмечена как оплаченная")
        return buyer_transaction

    @staticmethod
    def _freeze_seller_funds(ready_task: ReadyTask, net_amount):
        seller = ready_task.owner
        if not seller or not hasattr(seller, "wallet"):
            raise ValidationError({"purchase_ready_task_freeze_seller_funds": 'У продавца не найден кошелек'})

        seller_wallet = seller.wallet
        release_at = timezone.now() + timedelta(days=14)

        now = timezone.now()
        external_id = f"studium_rt_sell_{seller_wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

        transaction_data = {
            'external_id ': external_id,
            'wallet': seller_wallet.id,
            'amount': net_amount,
            'type': 'reward',
            'status': 'frozen',
        }

        serializer = TransactionCreateSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)

        seller_transaction = serializer.save()

        frozen_funds_data = {
            'wallet': seller_wallet.id,
            'transaction': seller_transaction.id,
            'amount': net_amount,
            'reason': f"Продажа работы {ready_task.id}",
            'release_at': release_at,
            'status': 'frozen'
        }

        frozen_serializer = FrozenFundsCreateSerializer(data=frozen_funds_data)
        frozen_serializer.is_valid(raise_exception=True)
        frozen_serializer.save(wallet=seller_wallet, transaction=seller_transaction)

        seller_wallet.frozen = (seller_wallet.frozen or 0) + net_amount
        seller_wallet.save(update_fields=["frozen"])

        return seller_transaction

    @staticmethod
    def _create_purchase_record(buyer_transaction, seller_transaction: Transaction,
                                ready_task: ReadyTask, net_amount, commission, amount):

        print(f"📝 Создание записи о покупке: транзакция={buyer_transaction.id}, работа={ready_task.id}")

        purchase_data = {
            'buyer_transaction': buyer_transaction.id,
            'seller_transaction': seller_transaction.id,
            'ready_task': ready_task.id,
            'payment_amount': amount,
            'commission': commission,
            'net_amount': net_amount,
            'status': 'paid'
        }

        serializer = PurchasedReadyTaskCreateSerializer(data=purchase_data)
        serializer.is_valid(raise_exception=True)
        purchase = serializer.save()

        print(f"✅ Запись о покупке {purchase.id} создана")
        return purchase


class SlotPackageListView(APIView):
    permission_classes = [AllowAny]

    @catch_and_log_exceptions
    def get(self, request):
        packages = SlotPackage.objects.filter(is_active=True).order_by('slots_count')
        serializer = SlotPackageSerializer(packages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BuySlotPackageView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    @catch_and_log_exceptions
    def post(self, request):
        user = request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        client = self._get_client(user)

        package_id = request.data.get('package_id')
        package = self._get_package(package_id)

        wallet = user.wallet
        self._check_balance(wallet, package.price)

        with transaction.atomic():
            txn, free_slots, balance = self.purchase_slots(wallet, client, package)

            client_data = {
                "email": user.email,
            }

            items = [
                {
                    "name": f"Пакет слотов {package.slots_count}",
                    "price": float(package.price),
                    "quantity": 1.0,
                    "sum": float(package.price),
                    "payment_method": "full_payment",
                    "payment_object": "service",
                    "vat": {"type": "none"},
                }
            ]

            AtolService.instance().create_regular_receipt(
                external_id=txn.external_id,
                total=float(package.price),
                items=items,
                client=client_data,
            )

        return Response({"status": "success"}, status=status.HTTP_200_OK)

    @staticmethod
    def _get_package(package_id: int) -> SlotPackage:
        if not package_id:
            raise ValidationError({"buy_slots_get_package": "Не передан ключ пакета"})
        package = SlotPackage.objects.filter(id=package_id).first()
        if not package:
            raise ValidationError({"buy_slots_get_package": "Пакет не найден"})
        if not package.is_active:
            raise ValidationError({"buy_slots_get_package": "Пакет не активен"})
        return package

    @staticmethod
    def _check_balance(wallet: Wallet, price: float):
        if wallet.balance < price:
            raise AppException(message='Недостаточно средств для покупки', status_code=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _get_client(user):
        client = getattr(user, 'client', None)
        if client is None:
            raise ValidationError({"buy_slots_get_client": "Пользователь не найден"})
        return client

    @transaction.atomic
    def purchase_slots(self, wallet: Wallet, client, package: SlotPackage):
        with transaction.atomic():
            now = timezone.now()
            external_id = f"studium_sl_buy_{wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"

            transaction_data = {
                'external_id': external_id,
                'wallet': wallet.id,
                'amount': package.price,
                'type': 'purchase_slots',
                'status': 'paid',
                'receipt_status': 'pending',
            }

            serializer = TransactionCreateSerializer(data=transaction_data)
            serializer.is_valid(raise_exception=True)
            txn = serializer.save(wallet=wallet)

            slots_purchase_data = {
                'transaction': txn.id,
                'status': 'paid',
                'count_slots': package.slots_count
            }

            slots_serializer = SlotsPurchaseCreateSerializer(data=slots_purchase_data)
            slots_serializer.is_valid(raise_exception=True)
            slots_serializer.save()

            wallet.balance = (wallet.balance or 0) - package.price
            wallet.save(update_fields=["balance"])

            client.free_slots = (client.free_slots or 0) + package.slots_count
            client.save(update_fields=["free_slots"])

            return txn, client.free_slots, wallet.balance


class TransactionHistoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(wallet__user=user).order_by('-created_at')

        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        start = (page - 1) * page_size
        end = start + page_size

        paginated_transactions = transactions[start:end]
        serializer = TransactionSerializer(paginated_transactions, many=True)

        return Response({
            'transactions': serializer.data,
            'total_count': transactions.count(),
            'has_next': end < transactions.count(),
            'has_previous': page > 1,
            'current_page': page,
            'page_size': page_size
        }, status=status.HTTP_200_OK)


class WithdrawalView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @catch_and_log_exceptions
    def post(self, request):
        print("=== [WITHDRAW START] ===")
        user = request.user

        if user.client.is_banned:
            return Response({'detail': 'Пользователь заблокирован'}, status=423)

        print("User:", user.id, user.email)
        wallet = user.wallet
        print("Wallet ID:", wallet.id, "Balance:", wallet.balance)

        data = request.data.get("data", {})
        print("Incoming data:", data)

        amount_decimal = self._validate_amount_and_balance(wallet, data)
        print("Validated amount:", amount_decimal)

        method, requisites, personal_data = self._validate_method_and_requisites(data)
        print("Method:", method)
        print("Requisites:", requisites)
        print("Personal data:", personal_data)

        with transaction.atomic():
            txn = self._create_transaction(wallet, amount_decimal)
            print("Local transaction created:", txn.id, txn.external_id, txn.amount, txn.status)

            payload = self._build_payload(amount_decimal, method, requisites, personal_data, txn.external_id)
            print("Payload for Jump Finance:", payload)

            webhook_status, webhook_response = self._send_withdraw_request(payload)
            print("Jump Finance response:", webhook_status, webhook_response)

            if webhook_status != 200 or not webhook_response.get("success"):
                print("Jump Finance withdraw failed!")
                raise AppException(message=f"Ошибка при выводе средств")

            wallet.balance -= amount_decimal
            wallet.save(update_fields=["balance"])
            txn.status = "paid"
            txn.save(update_fields=["status"])
            print("Transaction marked as PAID and wallet updated:", txn.id, wallet.balance)

        print("=== [WITHDRAW SUCCESS] ===")
        return Response(
            {
                "message": "Вывод средств совершен",
                "external_id": txn.external_id
            },
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def _validate_amount_and_balance(wallet: Wallet, data: dict) -> Decimal:
        amount = data.get("amount")
        print("[VALIDATE AMOUNT] Raw amount:", amount)
        if amount is None:
            raise ValidationError({"amount": "Не указана сумма"})

        try:
            amount_decimal = Decimal(str(amount))
        except Exception:
            raise ValidationError({"amount": "Некорректная сумма"})

        if amount_decimal <= 0:
            raise AppException("Сумма должна быть больше нуля", status_code=status.HTTP_400_BAD_REQUEST)

        if amount_decimal < Decimal("1000"):
            raise AppException("Минимальная сумма для вывода — 1000 рублей", status_code=status.HTTP_400_BAD_REQUEST)

        if (wallet.balance or 0) < amount_decimal:
            raise AppException("Недостаточно средств для вывода", status_code=status.HTTP_400_BAD_REQUEST)

        return amount_decimal

    @staticmethod
    def _validate_method_and_requisites(data):
        method = (data.get("method") or "").strip().lower()
        print("[VALIDATE METHOD] Method:", method)
        if method not in ("card", "phone", "sbp", "account"):
            raise ValidationError({"method": "Допустимые значения: card, phone, sbp, account"})

        bank_name = data.get("bank_id", "").strip()
        print("[VALIDATE METHOD] Bank name:", bank_name)
        try:
            bank = Bank.objects.get(name=bank_name)
            print("[VALIDATE METHOD] Bank found:", bank.bank_id)
        except Bank.DoesNotExist:
            print("[VALIDATE METHOD] Bank not found!")
            raise ValidationError({"bank_id": f"Банк '{bank_name}' не найден"})

        requisites = {
            "bank_id": bank.bank_id,
            "card_number": data.get("card_number", "").strip(),
            "phone_number": data.get("phone_number", "").strip(),
            "account_number": data.get("account_number", "").strip(),
        }
        print("[VALIDATE METHOD] Requisites:", requisites)

        personal_data = {
            "first_name": data.get("first_name", "").strip(),
            "last_name": data.get("last_name", "").strip(),
            "middle_name": data.get("middle_name", "").strip(),
        }
        print("[VALIDATE METHOD] Personal data:", personal_data)

        return method, requisites, personal_data

    @staticmethod
    def _create_transaction(wallet: Wallet, amount: Decimal) -> Transaction:
        now = timezone.now()
        external_id = f"studium_wd_{wallet.id}_{now.strftime('%Y.%m.%d.%H.%M.%S')}"
        print("[CREATE TRANSACTION] External ID:", external_id)

        transaction_data = {
            'external_id': external_id,
            'wallet': wallet.id,
            'amount': amount,
            'type': 'withdraw',
            'status': 'pending',
        }
        print("[CREATE TRANSACTION] Data:", transaction_data)

        serializer = TransactionCreateSerializer(data=transaction_data)
        serializer.is_valid(raise_exception=True)
        txn = serializer.save(wallet=wallet)
        print("[CREATE TRANSACTION] Saved txn:", txn.id)
        return txn

    @staticmethod
    def _build_payload(amount: Decimal, method: str, requisites: dict, personal_data: dict, external_id: str) -> dict:
        print("[BUILD PAYLOAD] Start")
        if method == "sbp":
            requisite = {
                "type_id": 10,
                'account_number': requisites.get("phone_number", ""),
                "sbp_bank_id": requisites.get("bank_id", ""),
            }
        else:
            requisite = {
                "type_id": 8,
                "account_number": requisites.get("card_number", "")
            }

        payload = {
            "customer_payment_id": external_id,
            "amount": float(amount),
            "first_name": personal_data.get("first_name", ""),
            "last_name": personal_data.get("last_name", ""),
            "phone": requisites.get("phone_number", ""),
            "requisite": requisite,
        }

        if personal_data.get("middle_name"):
            payload["middle_name"] = personal_data["middle_name"]

        print("[BUILD PAYLOAD] Result:", payload)
        return payload

    @staticmethod
    def _send_withdraw_request(payload: dict):
        url = f"{settings.JUMP_FINANCE_API_URL}/services/openapi/payments/smart"
        headers = {
            "Client-Key": settings.JUMP_FINANCE_API_TOKEN,
            "Content-Type": "application/json",
        }
        print("[SEND REQUEST] URL:", url)
        print("[SEND REQUEST] Headers:", headers)
        print("[SEND REQUEST] Payload:", payload)
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            print("[SEND REQUEST] Status:", response.status_code)
            print("[SEND REQUEST] Response:", response.text)
            return response.status_code, response.json()
        except Exception as e:
            print("WITHDRAWAL ERROR", str(e))
            return "error", {"error": str(e)}


@method_decorator(csrf_exempt, name="dispatch")
class AtolCallbackView(APIView):

    parser_classes = [JSONParser]

    @catch_and_log_exceptions
    def post(self, request):
        data = request.data
        print("🔔 Получено callback уведомление от АТОЛ:")
        print(f"📦 Данные: {data}")

        try:
            external_id = data.get('external_id')
            if not external_id:
                print("❌ Не найден external_id в callback данных")
                return Response({"error": "external_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            payment_transaction = self._find_transaction_by_external_id(external_id)
            if not payment_transaction:
                print(f"❌ Транзакция не найдена для external_id: {external_id}")
                return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

            receipt_status = data.get('status')
            if receipt_status == 'done':
                payment_transaction.receipt_status = 'sent'
                payment_transaction.save(update_fields=["receipt_status"])
                print(f"✅ Чек отмечен как отправленный для транзакции {payment_transaction.id}")

            elif receipt_status == 'fail':
                payment_transaction.receipt_status = 'failed'
                payment_transaction.save(update_fields=["receipt_status"])
                print(f"❌ Ошибка отправки чека для транзакции {payment_transaction.id}")

                message = (
                    f"❌ Ошибка отправки чека!\n\n"
                    f"ID транзакции: {payment_transaction.id}\n"
                    f"Сумма: {payment_transaction.amount}\n"
                    f"Тип: {payment_transaction.type}\n"
                    f"External ID: {payment_transaction.external_id}\n"
                    f"Статус чека: failed\n\n"
                    f"📦 Полный ответ АТОЛ:\n{data}"
                )
                send_telegram_message(message)

            else:
                payment_transaction.receipt_status = 'pending'
                payment_transaction.save(update_fields=["receipt_status"])
                print(f"ℹ️ Статус чека обновлён как pending для транзакции {payment_transaction.id}")

            return Response({"status": "success"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"🛑 Ошибка при обработке callback от АТОЛ: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def _find_transaction_by_external_id(external_id):
        try:
            return Transaction.objects.filter(external_id=external_id).first()
        except Exception as e:
            print(f"❌ Ошибка при поиске транзакции по external_id {external_id}: {e}")
        return None

