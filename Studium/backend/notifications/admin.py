from django.contrib import admin
from django.utils.html import format_html
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Notification, FailureNotification


class NotificationInline(GenericTabularInline):
    model = Notification
    extra = 0
    readonly_fields = ("user", "message", "content", "category", "is_read", "created_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "content", "is_read", "created_at", "target_object_link")
    list_filter = ("is_read", "content", "created_at")
    search_fields = ("user__username", "message")
    readonly_fields = ("created_at", "target_object_link")

    fieldsets = (
        (None, {"fields": ("user", "message", "content")}),
        ("Связанная модель", {"fields": ("content_type", "object_id", "target_object_link")}),
        ("Статус", {"fields": ("is_read", "auto_read", "created_at")}),
    )

    def target_object_link(self, obj):
        if obj.content_type and obj.object_id:
            related_model = obj.content_type.model_class()
            if related_model:
                related_object = related_model.objects.filter(id=obj.object_id).first()
                if related_object:
                    url = f"/admin/{obj.content_type.app_label}/{obj.content_type.model}/{obj.object_id}/change/"
                    return format_html('<a href="{}">{}</a>', url, related_object)
        return "-"

    target_object_link.short_description = "Связанный объект"


@admin.register(FailureNotification)
class FailureNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'is_read', 'auto_read', 'created_at', 'truncated_message')
    list_filter = ('is_read', 'auto_read', 'created_at', 'user')
    search_fields = ('message', 'failure_message', 'user__username', 'content')
    list_per_page = 20
    date_hierarchy = 'created_at'

    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'content', 'is_read', 'auto_read')
        }),
        ('Сообщения', {
            'fields': ('message', 'failure_message'),
            'classes': ('wide',),
        }),
        ('Дополнительная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def truncated_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message

    truncated_message.short_description = 'Сообщение (кратко)'