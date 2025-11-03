
from django.urls import path
from .views import BalanceTopUpView, TinkoffNotificationView, PurchaseReadyTask, SlotPackageListView, \
    BuySlotPackageView, TransactionHistoryView, WithdrawalView, AtolCallbackView

urlpatterns = [
    path("start_payment/", BalanceTopUpView.as_view(), name="start_payment"),
    path("buy_ready_task/", PurchaseReadyTask.as_view(), name="ready_task_payment"),
    path("tinkoff_notify/", TinkoffNotificationView.as_view(), name="tinkoff_notification"),
    path("atol_callback/", AtolCallbackView.as_view(), name="atol_callback"),
    path("slot_packages/", SlotPackageListView.as_view(), name="slot_packages_list"),
    path("buy_slot_package/", BuySlotPackageView.as_view(), name="buy_slot_package"),
    path("transactions/", TransactionHistoryView.as_view(), name="transaction_history"),
    path("withdrawal/", WithdrawalView.as_view(), name="withdrawal"),
]
