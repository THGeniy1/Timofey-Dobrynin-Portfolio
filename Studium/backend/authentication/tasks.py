from celery import shared_task
import logging

from .utils import sync_selectel_admins

logger = logging.getLogger(__name__)


@shared_task(name="authentication.tasks.sync_selectel_admins_daily")
def sync_selectel_admins_daily():
	result = sync_selectel_admins()
	logger.info("Selectel admins sync result: %s", result)
	return result
