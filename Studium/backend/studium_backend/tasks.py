import os
from django.conf import settings
from datetime import datetime, timedelta

from celery import shared_task


@shared_task()
def delete():
    folder_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
    now = datetime.now()

    if not os.path.exists(folder_path):
        return

    for folder in os.listdir(folder_path):
        folder_full_path = os.path.join(folder_path, folder)

        if os.path.isdir(folder_full_path):
            for filename in os.listdir(folder_full_path):
                file_path = os.path.join(folder_full_path, filename)

                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                    if now - file_time > timedelta(minutes=1):
                        os.remove(file_path)
