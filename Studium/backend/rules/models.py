from django.db import models


class Rules(models.Model):
    TYPE_CHOICES = [
        ('rules', 'Правила'),
        ("offer", "Оферта"),
        ("privacy_politic", "Политика приватности"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.TextField(blank=False, null=False, unique=True)
    path = models.TextField(blank=False, null=False, unique=True)

    create_date = models.DateTimeField(auto_now_add=True)
