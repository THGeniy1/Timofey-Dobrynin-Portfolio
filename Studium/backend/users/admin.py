from django.contrib import admin
from authentication.models import UserChangeLog


@admin.register(UserChangeLog)
class UserChangeLogAdmin(admin.ModelAdmin):
    list_display = ("user", "field_name", "old_value", "new_value", "changed_at")
    list_filter = ("field_name", "changed_at", "user")
    search_fields = ("user__name", "field_name", "old_value", "new_value")
    readonly_fields = ("user", "field_name", "old_value", "new_value", "changed_at")
    ordering = ("-changed_at",)
    date_hierarchy = "changed_at"
