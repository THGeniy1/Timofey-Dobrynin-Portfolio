from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from .models import JsonFile
from .json_service import JsonService
from storage.mixins import PrivateUploadMixin


class JsonFileForm(forms.ModelForm, PrivateUploadMixin):
    file = forms.FileField(required=True, label="Загрузить JSON-файл")

    class Meta:
        model = JsonFile
        fields = ['name']

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get('file')

        if uploaded_file:
            file_path = f"jsons/{uploaded_file.name}"
            self.upload_file(file_path, uploaded_file)

            instance.path = file_path

            if not instance.name:
                instance.name = uploaded_file.name

        if commit:
            instance.save()

            json_service = JsonService()
            json_service.refresh_json(instance.name)

        return instance


@admin.register(JsonFile)
class JsonFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'created_at', 'updated_at', 'download_link')
    readonly_fields = ('created_at', 'updated_at', 'download_link')
    form = JsonFileForm

    def download_link(self, obj):
        if obj.path:
            return mark_safe(f'<a href="/media/{obj.path}" download>Скачать</a>')
        return "-"

    download_link.short_description = "Скачать"
