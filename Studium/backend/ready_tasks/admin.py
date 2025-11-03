from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.loader import render_to_string

from .models import ReadyTask


@admin.register(ReadyTask)
class ReadyTaskAdmin(admin.ModelAdmin):

    list_display = ("name", "owner", "discipline", "price", "create_date", "status")
    list_filter = ("discipline", "city", "university", "status")
    search_fields = ("name", "description", "owner__email", "university", "faculty")
    ordering = ("-create_date",)

    fieldsets = (
        ("Основная информация", {"fields": ("owner", "name", "discipline", "type", "description")}),
        ("Учебное заведение", {"fields": ("city", "university", "faculty", "direction", "level")}),
        ("Дополнительно", {"fields": ("tutor", "score", "price", "previous_version")}),
        ("Системные данные", {"fields": ("create_date", "status")}),
        ("Работа с файлами", {"fields": ("archive_actions",)}),
    )

    readonly_fields = ("create_date", "archive_actions")
    change_form_template = "admin/ready_task/ready_task_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/download_archive/',
                self.admin_site.admin_view(self.download_archive),
                name='ready_task_download_archive'
            ),
        ]
        return custom_urls + urls

    def archive_actions(self, obj=None):
        if not obj or not obj.pk:
            return "Доступно после сохранения работы"

        download_url = reverse('archive-download', args=[obj.id]) + '?type=ready_task'

        context = {
            'download_url': download_url,
        }

        return render_to_string('admin/ready_task/archive_download_button.html', context)

    archive_actions.short_description = "Управление архивом"
    archive_actions.allow_tags = True

    def download_archive(self, request, object_id):
        task = self.get_object(request, object_id)
        download_url = reverse('archive-download', args=[task.id]) + '?type=ready_task'
        return HttpResponseRedirect(download_url)
