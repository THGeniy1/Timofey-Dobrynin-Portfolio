from celery import shared_task
from celery.worker.state import requests
from django.utils import timezone
import logging

from django.db import transaction as db_transaction
from django.db.models import F

from studium_backend import settings
from .models import FrozenFunds, Wallet, Transaction

logger = logging.getLogger(__name__)


@shared_task
def release_expired_frozen_funds():
    now = timezone.now()
    released_count = 0

    candidates = FrozenFunds.objects.filter(
        status='frozen',
        release_at__lte=now,
    ).select_related('wallet').order_by('created_at')

    for frozen_funds in candidates:
        try:
            with db_transaction.atomic():
                ff = FrozenFunds.objects.select_for_update().select_related('wallet').get(
                    id=frozen_funds.id,
                    status='frozen',
                    release_at__lte=now
                )

                wallet = ff.wallet

                Wallet.objects.filter(id=wallet.id).update(
                    balance=F('balance') + ff.amount,
                    frozen=F('frozen') - ff.amount,
                )

                ff.status = 'released'
                ff.save(update_fields=['status'])

                released_count += 1

        except FrozenFunds.DoesNotExist:
            continue
        except Exception as e:
            logger.exception(f"Ошибка при разблокировке FrozenFunds(id={frozen_funds.id}): {e}")
            continue

    logger.info(f"Разблокировано записей FrozenFunds: {released_count}")


@shared_task
def expire_pending_payments():
    expired_count = 0
    now = timezone.now()

    pending_transactions = Transaction.objects.filter(status="pending")

    for tx in pending_transactions:
        if tx.is_expired(hours=1):
            with db_transaction.atomic():
                tx.mark_as_canceled(save=True)
                expired_count += 1

    return f"Expired {expired_count} pending transactions at {now}"


@shared_task
def check_withdrawals_status():

    pending_withdrawals = Transaction.objects.filter(
        type="withdraw", status="pending"
    )

    for trx in pending_withdrawals:
        try:
            url = f"{settings.JUMP_FINANCE_API_URL}/v1/payments/customer/{trx.external_id}"
            headers = {
                "Client-Key": settings.JUMP_FINANCE_API_TOKEN,
                "Accept": "application/json",
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            print("PAYMENT DATA", data)
            payment_status = data.get("status", "").lower()

            with db_transaction.atomic():
                if payment_status in ("done", "paid", "success"):
                    trx.status = "paid"
                    trx.save(update_fields=["status"])
                else:
                    trx.status = "failed"
                    trx.save(update_fields=["status"])
                    wallet = trx.wallet
                    wallet.balance = (wallet.balance or 0) + trx.amount
                    wallet.save(update_fields=["balance"])

        except Exception as e:
            trx.mark_as_failed()
            wallet = trx.wallet
            wallet.balance = (wallet.balance or 0) + trx.amount
            wallet.save(update_fields=["balance"])
            print(f"[WITHDRAW CHECK] Ошибка при обработке {trx.id}: {e}")

