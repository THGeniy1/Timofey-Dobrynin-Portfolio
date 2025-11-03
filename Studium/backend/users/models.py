from django.db import models


class Education(models.Model):
    city = models.CharField(max_length=255, blank=False)
    university = models.CharField(max_length=255, blank=False)
    faculty = models.CharField(max_length=255, blank=False)
    direction = models.CharField(max_length=255, blank=False)
    level = models.CharField(max_length=255, blank=False)
    active = models.BooleanField(default=True)
    create_date = models.DateTimeField(auto_now_add=True)
