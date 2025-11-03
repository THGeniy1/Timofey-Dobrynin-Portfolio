from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse

from storage.mixins import FileUploadMixin
from .models import Rules


class RulesAdminForm(forms.ModelForm):
    upload_file = forms.FileField(required=False, label="Загрузить новый файл")

    class Meta:
        model = Rules
        fields = ("type", "upload_file")

    def clean_upload_file(self):
        file = self.cleaned_data.get('upload_file')

        return file


@admin.register(Rules)
class RulesAdmin(admin.ModelAdmin):
    form = RulesAdminForm

    list_display = ("name", "type", "create_date")
    list_filter = ("type", "create_date")
    search_fields = ("name", "path")
    ordering = ("-create_date",)

    class FileUploader(FileUploadMixin):
        _upload_direction = "public/rules"
        _ALLOWED_FILE_EXTENSIONS = ['.pdf', '.docx']
        _storage_type = "public"

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                (None, {
                    "fields": ("type", "name", "path", "create_date", "download_link")
                }),
            )
        else:
            return (
                (None, {
                    "fields": ("type", "upload_file")
                }),
            )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return "name", "path", "create_date", "download_link"
        else:
            return ()

    def save_model(self, request, obj, form, change):
        upload_file = form.cleaned_data.get("upload_file")

        if upload_file:
            uploader = self.FileUploader()
            response = uploader.upload_file(file=upload_file, user=request.user)
            if response.status_code == 200:
                file_path = response.data["file_path"]
                obj.path = file_path

                if not obj.name:
                    obj.name = upload_file.name
            else:
                raise Exception(f"Ошибка загрузки файла в S3: {response.data.get('error', 'Неизвестная ошибка')}")

        super().save_model(request, obj, form, change)

    def download_link(self, obj=None):
        if obj and obj.pk:
            download_url = reverse('archive-download-public', args=[obj.id]) + '?type=rules'
            return format_html('<a href="{}" class="button">Скачать файл</a>', download_url)
        return "Нет файла для скачивания"

    download_link.short_description = "Скачать файл"
