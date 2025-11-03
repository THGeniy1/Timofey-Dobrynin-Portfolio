from django.db import models
from authentication.models import CustomUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Report(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ("pending", "В ожидании"),
        ("ending", "Завершено"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")
    type = models.CharField(max_length=20, null=False, blank=False, default="report", verbose_name="Тип жалобы")

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="complaints", verbose_name="Жалобщик")
    reported_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reported_complaints",
                                      null=True, blank=True, verbose_name="Обвиняемый")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Жалоба #{self.id} от {self.user} на {self.reported_user or 'Не указано'}"

    class Meta:
        verbose_name = "Жалоба"
        verbose_name_plural = "Жалобы"
        ordering = ["-created_at"]


class ReportComment(models.Model):
    report = models.ForeignKey(Report, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.TextField()
    is_admin = models.BooleanField(default=False, verbose_name="Админский комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Комментарий #{self.id} к жалобе #{self.report.id}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created_at"]


class Files(models.Model):
    comment = models.ForeignKey(ReportComment, related_name='files', on_delete=models.CASCADE)
    name = models.TextField()
    path = models.TextField(max_length=1000, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Файл для комментария #{self.comment.id}"

    class Meta:
        verbose_name = "Файл комментария"
        verbose_name_plural = "Файлы комментариев"
