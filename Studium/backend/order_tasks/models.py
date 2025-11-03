from django.db import models
from django.db.models import F
from authentication.models import CustomUser


class OrderTask(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активно'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
        ('review', 'На проверке'),
        ('unpublished', 'Снято с публикации'),
    ]

    owner = models.ForeignKey(CustomUser, on_delete=models.PROTECT, blank=True, null=True)

    name = models.CharField('Название задания', max_length=200)
    description = models.TextField('Описание', blank=True, null=True)
    discipline = models.CharField('Дисциплина', max_length=200, blank=True)
    type = models.CharField('Тип работы', max_length=200, blank=True)

    city = models.CharField('Город', max_length=200, blank=True)
    university = models.CharField('Университет', max_length=200, blank=True)
    faculty = models.CharField('Факультет', max_length=200, blank=True)
    direction = models.CharField('Направление', max_length=200, blank=True)
    level = models.CharField('Уровень подготовки', max_length=200, blank=True)
    tutor = models.CharField('Преподаватель', max_length=200, blank=True)

    price = models.DecimalField('Бюджет', max_digits=10, decimal_places=2, default=0)

    deadline = models.DateTimeField('Дедлайн', blank=True, null=True)
    publish_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated_at = models.DateTimeField('Последнее обновление', auto_now=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='review')
    executor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True,
                                 related_name='tasks_taken', verbose_name='Исполнитель')

    views = models.PositiveIntegerField(default=0)

    def get_latest_version(self):
        latest = self
        while latest.new_versions.exists():
            latest = latest.new_versions.last()
        return latest

    def increment_views(self):
        self.__class__.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.refresh_from_db(fields=['views'])
        return self.views

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    class Meta:
        ordering = ['-publish_date']
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'


class Files(models.Model):
    task = models.ForeignKey(OrderTask, on_delete=models.CASCADE, related_name='files', blank=True)
    name = models.TextField()
    size = models.CharField(max_length=50)
    path = models.TextField(max_length=1000, blank=True)
    is_public = models.BooleanField()
    create_date = models.DateTimeField(auto_now_add=True)
