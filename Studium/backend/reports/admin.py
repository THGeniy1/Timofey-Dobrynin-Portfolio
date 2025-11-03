from django.contrib import admin
from django.template.loader import render_to_string
from django.urls import reverse
from .models import Report, ReportComment, Files


class FilesInline(admin.TabularInline):
    model = Files
    extra = 0
    readonly_fields = ("create_date",)
    fields = ("name", "path", "create_date")


class ReportCommentInline(admin.StackedInline):
    model = ReportComment
    extra = 0
    readonly_fields = ("created_at", "download_button")
    fields = ("user", "comment", "is_admin", "created_at", "download_button")
    inlines = [FilesInline]

    def download_button(self, obj):
        if obj and obj.pk:
            download_url = reverse('archive-download', args=[obj.id]) + '?type=report_comment'
            return render_to_string('admin/reports/archive_download_button.html', {'download_url': download_url})
        return "Нет файлов для скачивания"

    download_button.short_description = "Скачать файлы"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "reported_user", "status", "created_at", "type")
    list_filter = ("status", "type", "created_at")
    search_fields = ("user__username", "reported_user__username", "id")
    readonly_fields = ("created_at",)
    inlines = [ReportCommentInline]
    change_form_template = "admin/reports/report_form.html"

    fieldsets = (
        (None, {
            "fields": ("status", "type", "user", "reported_user", "content_type", "object_id", "created_at")
        }),
    )
