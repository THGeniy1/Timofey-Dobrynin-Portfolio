from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.loader import render_to_string

from .models import OrderTask


@admin.register(OrderTask)
class OrderTaskAdmin(admin.ModelAdmin):

    list_display = ("name", "owner", "discipline", "price", "publish_date", "status")
    list_filter = ("discipline", "city", "university", "status")
    search_fields = ("name", "description", "owner__email", "university", "faculty")
    ordering = ("-publish_date",)

    fieldsets = (
        ("Основная информация", {
            "fields": ("owner", "name", "discipline", "type", "description")
        }),
        ("Учебное заведение", {
            "fields": ("city", "university", "faculty", "direction", "level")
        }),
        ("Дополнительно", {
            "fields": ("tutor", "executor", "price", "deadline")
        }),
        ("Системные данные", {
            "fields": ("publish_date", "updated_at", "status", "views")
        }),
        ("Работа с файлами", {
            "fields": ("archive_actions",)
        }),
    )

    readonly_fields = ("publish_date", "updated_at", "views", "archive_actions")
    change_form_template = "admin/order_task/order_task_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/download_archive/',
                self.admin_site.admin_view(self.download_archive),
                name='order_task_download_archive'
            ),
        ]
        return custom_urls + urls

    def archive_actions(self, obj=None):
        if not obj or not obj.pk:
            return "Доступно после сохранения задания"

        download_url = reverse('archive-download', args=[obj.id]) + '?type=order_task'

        context = {
            'download_url': download_url,
        }
        return render_to_string('admin/order_task/archive_download_button.html', context)

    archive_actions.short_description = "Управление архивом"
    archive_actions.allow_tags = True

    def download_archive(self, request, object_id):
        task = self.get_object(request, object_id)
        download_url = reverse('archive-download', args=[task.id]) + '?type=order_task'
        return HttpResponseRedirect(download_url)
