from django.db import models


class JsonFile(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    path = models.CharField(max_length=255, blank=False, null=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
