from django.contrib import admin
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "reviewer", "rating", "created_at")
    list_display_links = ("id",)
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "reviewer__username", "comment")
    readonly_fields = ("created_at",)
    fieldsets = (
        ("Основная информация", {"fields": ("user", "reviewer", "rating", "comment")}),
        ("Связь с объектом", {"fields": ("content_type", "object_id"), "classes": ("collapse",)}),
        ("Системные данные", {"fields": ("created_at",)}),
    )
