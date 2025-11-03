import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studium_backend.settings')

app = Celery('studium_celery')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'delete-old-notifications-daily': {
        'task': 'notifications.tasks.delete_old_notifications',
        'schedule': crontab(hour=0, minute=0),
    },
    'expire-pending-payments-daily': {
        'task': 'payments.tasks.expire_pending_payments',
        'schedule': crontab(hour=0, minute=0),
    },
    'release-expired-frozen-funds-hourly': {
        'task': 'payments.tasks.release_expired_frozen_funds',
        'schedule': crontab(minute=0), 
    },
    'sync-selectel-admins-daily': {
        'task': 'authentication.tasks.sync_selectel_admins_daily',
        'schedule': crontab(hour=1, minute=0),
    },
    'check-withdrawals-daily': {
        "task": "payments.tasks.check_withdrawals_status",
        "schedule": crontab(hour=3, minute=0),
    },

}


@worker_ready.connect
def run_sync_selectel_admins_on_start(sender=None, **kwargs):
    try:
        sender.app.send_task('authentication.tasks.sync_selectel_admins_daily', countdown=10)
    except Exception:
        pass
