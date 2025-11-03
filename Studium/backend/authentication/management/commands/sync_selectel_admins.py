from django.core.management.base import BaseCommand

from authentication.utils import sync_selectel_admins


class Command(BaseCommand):
	help = "Synchronize admins from Selectel into local database"

	def handle(self, *args, **options):
		result = sync_selectel_admins()
		self.stdout.write(self.style.SUCCESS(f"Sync completed: {result}"))
