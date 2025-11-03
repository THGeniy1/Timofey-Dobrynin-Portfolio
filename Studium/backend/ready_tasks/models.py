from django.db import models
from authentication.models import CustomUser


class ReadyTask(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активно'),
        ('unpublished', 'Снято с публикации'),
        ('review', 'На проверке'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.PROTECT, blank=True, null=True)

    name = models.CharField(max_length=200)
    discipline = models.CharField(max_length=200)

    type = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    city = models.CharField(max_length=200)
    university = models.CharField(max_length=200)
    faculty = models.CharField(max_length=200)
    direction = models.CharField(max_length=200)
    level = models.CharField(max_length=200)

    tutor = models.CharField(max_length=200)

    score = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    create_date = models.DateTimeField(auto_now_add=True)

    previous_version = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True, related_name='new_versions'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='review')

    views = models.PositiveIntegerField(default=0)

    def get_latest_version(self):
        latest = self
        while latest.new_versions.exists():
            latest = latest.new_versions.last()
        return latest

    def increment_views(self):
        from django.db.models import F
        from django.db import transaction
        
        with transaction.atomic():
            ReadyTask.objects.filter(pk=self.pk).update(views=F('views') + 1)
            self.refresh_from_db(fields=["views"])
        return self.views


class Files(models.Model):
    task = models.ForeignKey(ReadyTask, on_delete=models.CASCADE, related_name='files', blank=True)
    name = models.TextField()
    size = models.CharField(max_length=50)
    path = models.TextField(max_length=1000, blank=True)
    is_public = models.BooleanField()
    create_date = models.DateTimeField(auto_now_add=True)


class PlacementPackage(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="placement_packages")
    total_slots = models.PositiveIntegerField(help_text="Общее количество мест для размешения")
    used_slots = models.PositiveIntegerField(default=0, help_text="Сколько мест уже использовано")

    class Meta:
        verbose_name = "Пакет мест"
        verbose_name_plural = "Пакеты мест"

    @property
    def available_slots(self):
        return self.total_slots - self.used_slots

    def use_slot(self, count=1):
        if self.available_slots < count:
            raise ValueError("Недостаточно доступных мест")
        self.used_slots += count
        self.save(update_fields=["used_slots"])

    def release_slot(self, count=1):
        self.used_slots = max(self.used_slots - count, 0)
        self.save(update_fields=["used_slots"])
