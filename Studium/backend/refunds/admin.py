from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.loader import render_to_string

from .models import Refund
from .views import RefundProcessView


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'purchase',
        'status',
        'get_contact_display',
        'reason',
        'admin_comment',
        'keep_product',
        'is_admin_created',
        'requested_at',
        'processed_at',
        'completed_at',
        'processed_by',
    )

    list_filter = ('status', 'requested_at', 'processed_at', 'completed_at', 'keep_product', 'is_admin_created')
    search_fields = ('purchase__id', 'contact_info', 'reason', 'admin_comment')

    readonly_fields = (
        'requested_at',
        'processed_at',
        'completed_at',
        'archive_actions',
        'process_actions'
    )

    actions = [
        'mark_as_processing',
        'mark_as_approved',
        'mark_as_completed',
        'mark_as_rejected',
        'mark_as_failed',
    ]

    change_form_template = "admin/refunds/refund_form.html"

    fieldsets = (
        (None, {
            'fields': ('purchase', 'status', 'reason', 'contact_info')
        }),
        ('Административные данные', {
            'fields': (
                'admin_comment', 'processed_by', 'processed_at', 'completed_at', 'keep_product', 'is_admin_created'
            )
        }),
        ('Доступ к файлам и действия', {
            'fields': ('archive_actions', 'process_actions')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/download_archive/',
                self.admin_site.admin_view(self.download_archive),
                name='refund_download_archive'
            ),
            path(
                '<path:object_id>/process_action/',
                self.admin_site.admin_view(self.process_action),
                name='refunds_refund_process_action'
            ),
        ]
        return custom_urls + urls

    def archive_actions(self, obj=None):
        if not obj or not obj.pk:
            return "Доступно после сохранения возврата"

        download_url = reverse('archive-download', args=[obj.id]) + '?type=refund'
        context = {'download_url': download_url}
        return render_to_string('admin/refunds/archive_download_button.html', context)

    archive_actions.short_description = "Файлы возврата"
    archive_actions.allow_tags = True

    def process_actions(self, obj=None):
        if not obj or not obj.pk:
            return "Доступно после сохранения возврата"

        def build_url(action):
            return reverse('admin:refunds_refund_process_action', args=[obj.id]) + f"?action={action}"

        context = {
            'processing_url': build_url('processing'),
            'approve_url': build_url('approve'),
            'reject_url': build_url('reject'),
            'fail_url': build_url('fail'),
            'complete_url': build_url('complete'),
        }
        return render_to_string('admin/refunds/refund_process_buttons.html', context)

    process_actions.short_description = "Управление возвратом"
    process_actions.allow_tags = True

    def download_archive(self, request, object_id):
        refund = self.get_object(request, object_id)
        if not refund:
            messages.error(request, "Возврат не найден")
            return HttpResponseRedirect(reverse('admin:refunds_refund_changelist'))

        download_url = reverse('archive-download', args=[refund.id]) + '?type=refund'
        return HttpResponseRedirect(download_url)

    def process_action(self, request, object_id):
        refund = self.get_object(request, object_id)
        if not refund:
            messages.error(request, "Возврат не найден")
            return HttpResponseRedirect(reverse('admin:refunds_refund_changelist'))

        action = request.GET.get('action')
        comment = request.GET.get('comment')

        try:
            if action == 'processing':
                refund.mark_as_processing()
                messages.success(request, "Возврат переведен в обработку")
            elif action == 'approve':
                try:
                    view = RefundProcessView()
                    view._approve_refund(refund, request.user)
                    messages.success(
                        request,
                        "Возврат одобрен. Средства возвращены покупателю и списаны у продавца."
                    )
                except Exception as exc:
                    messages.error(request, f"Ошибка при одобрении возврата: {exc}")
            elif action == 'reject':
                refund.mark_as_rejected(user=request.user, comment=comment)
                messages.success(request, "Возврат отклонён")
            elif action == 'fail':
                refund.mark_as_failed()
                messages.success(request, "Возврат отмечен как ошибка")
            elif action == 'complete':
                refund.mark_as_completed()
                messages.success(request, "Возврат завершён")
            else:
                messages.error(request, "Некорректное действие")
        except Exception as exc:
            messages.error(request, f"Ошибка при выполнении действия: {exc}")

        return HttpResponseRedirect(reverse('admin:refunds_refund_change', args=[refund.id]))

    def get_contact_display(self, obj):
        if obj.contact_info:
            return obj.contact_info
        buyer_user = getattr(obj.purchase.buyer_transaction, 'user', None)
        if buyer_user and getattr(buyer_user, 'email', None):
            return f"{buyer_user.email} (из профиля)"
        return "Не указано"

    get_contact_display.short_description = "Контакт"

    @admin.action(description='Пометить как "В обработке"')
    def mark_as_processing(self, request, queryset):
        for refund in queryset:
            refund.mark_as_processing()

    @admin.action(description='Одобрить возврат')
    def mark_as_approved(self, request, queryset):
        for refund in queryset:
            refund.mark_as_approved(user=request.user)

    @admin.action(description='Завершить возврат')
    def mark_as_completed(self, request, queryset):
        for refund in queryset:
            refund.mark_as_completed()

    @admin.action(description='Отклонить возврат')
    def mark_as_rejected(self, request, queryset):
        for refund in queryset:
            refund.mark_as_rejected(user=request.user)

    @admin.action(description='Пометить как "Ошибка"')
    def mark_as_failed(self, request, queryset):
        for refund in queryset:
            refund.mark_as_failed()
