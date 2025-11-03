from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from notifications.utils import create_notification, send_user_email

from authentication.models import CustomUser
from ready_tasks.models import ReadyTask
from payments.models import PurchasedReadyTask
from feedbacks.models import Feedback
from reports.models import Report
from refunds.models import Refund


@receiver(post_save, sender=CustomUser)
def send_welcome_notification(sender, instance, created, **kwargs):
    content_type = ContentType.objects.get_for_model(CustomUser)
    if created:
        message = "Добро пожаловать в наш сервис! 🎉"
        content = "user"
        auto_read = True

    else:
        message = "Информация об пользователе обновлена!"
        content = "user"
        auto_read = False

    create_notification(user=instance, content_type=content_type, object_id=instance.id,
                        message=message, content=content, auto_read=auto_read)


@receiver(post_save, sender=ReadyTask)
def notify_task_update(sender, instance, created, **kwargs):
    if not created and kwargs.get('update_fields') == ['views']:
        return

    message = None
    auto_read = None

    content_type = ContentType.objects.get_for_model(instance)
    content = "ready_task"

    if created and not instance.previous_version and instance.status == 'review':
        message = f"Ваша работа {instance.id} на проверке и будет размещена после нее"
        auto_read = True

    elif not created and not instance.previous_version and instance.status == 'active':
        message = f"Размещена новая работа {instance.id}"
        auto_read = True

        send_user_email(
            user=instance.owner,
            subject="Ваша работа размещена!",
            message=f"Поздравляем! Ваша работа id:{instance.id} размещена на сайте Studium."
        )

    elif created and instance.previous_version and instance.status == 'review':
        message = f"Обновление работы id {instance.previous_version.id} на проверке"
        auto_read = False
    elif not created and instance.previous_version and instance.status == 'active':
        message = f"Работа id {instance.previous_version.id} обновлена, новый id {instance.id}"
        auto_read = False

        send_user_email(
            user=instance.owner,
            subject="Ваша работа обновлена!",
            message=f"Поздравляем! Ваша работа id {instance.previous_version.id} обновлена, новый id {instance.id}."
        )

    elif not created:
        try:
            old_instance = ReadyTask.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                if instance.status == 'active':
                    message = f"Ваша работа id:{instance.id} прошла проверку и размещена"
                elif instance.status == 'unpublished':
                    message = f"Ваша работа id:{instance.id} снята с публикации"
                auto_read = False
            else:
                changed_fields = []
                for field in ReadyTask._meta.fields:
                    field_name = field.name
                    if getattr(old_instance, field_name) != getattr(instance, field_name):
                        changed_fields.append(field_name)

                if changed_fields:
                    message = f"В вашей работе {instance.id} были внесены изменения администратором"
                    auto_read = False
                else:
                    return

        except ReadyTask.DoesNotExist:
            pass

    if message and content:
        create_notification(user=instance.owner, content_type=content_type, object_id=instance.id,
                            message=message, content=content, auto_read=auto_read or False)


@receiver(post_save, sender=PurchasedReadyTask)
def buy_notifications(sender, instance, created, **kwargs):
    if created and instance.status == 'paid':
        content_type = ContentType.objects.get_for_model(instance)
        content = "purchased_task"
        auto_read = False

        # Покупателю
        buyer_message = f"Поздравляю с покупкой работы id {instance.ready_task.id}"
        create_notification(
            user=instance.buyer_transaction.wallet.user,
            content_type=content_type,
            object_id=instance.id,
            message=buyer_message,
            content=content,
            auto_read=auto_read
        )

        # Продавцу
        seller_user = getattr(instance.ready_task, 'owner', None) or instance.seller_transaction.wallet.user
        seller_message = f"У вашей работы id {instance.ready_task.id} новая покупка"
        create_notification(
            user=seller_user,
            content_type=content_type,
            object_id=instance.id,
            message=seller_message,
            content=content,
            auto_read=auto_read
        )

        send_user_email(
            user=seller_user,
            subject="Покупка работы!",
            message=f"У вашей работы id {instance.ready_task.id} новая покупка!"
        )


@receiver(post_save, sender=Feedback)
def feedback_notifications(sender, instance, created, **kwargs):
    if created:
        print("Создаю уведомление об покупке")
        try:
            content_type = ContentType.objects.get_for_model(instance)
            created_message = f"Ваш отзыв на работу id:{instance.object_id}, успешно размещен🎉"
            content = "feedback"
            auto_read = True

            create_notification(user=instance.user, content_type=content_type, object_id=instance.id,
                                message=created_message, content=content, auto_read=auto_read)
        except Exception as e:
            print("Ошибка при создании уведомления об отзыве", e)


@receiver(post_save, sender=Report)
def report_notifications(sender, instance, created, **kwargs):
    if created:
        content_type = ContentType.objects.get_for_model(instance)

        if instance.type == "report":
            created_message = f"Ваша жалоба успешно размещена. Мы рассмотрим её в ближайшее время."
        else:
            created_message = f"Спасибо за предложение! " \
                              f"Мы ценим вашу инициативу и обязательно рассмотрим ваше предложение."

        content = "report"
        auto_read = True

        create_notification(user=instance.user, content_type=content_type, object_id=instance.id,
                            message=created_message, content=content, auto_read=auto_read)


@receiver(post_save, sender=Refund)
def refund_notifications(sender, instance, created, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    ready_task_id = instance.purchase.ready_task.id
    message = None
    content = "refund"
    auto_read = True

    if created and not instance.is_admin_created:
        message = f"Ваша заявка на возврат работы id:{ready_task_id}, размещена"

    elif not created and instance.status == 'rejected':
        message = f"Ваша заявка на возврат работы id:{ready_task_id}, отклонена"

    elif not created and instance.status == 'approved':
        if instance.keep_product:
            message = f"За работу id:{ready_task_id}, произведен возврат средств из-за ошибки в системе. " \
                      f"Купленная работа оставлена вам в подарок"

            send_user_email(
                user=instance.purchase.buyer_transaction.wallet.user,
                subject="Возврат средств!",
                message=f"За работу id:{ready_task_id}, произведен возврат средств из-за ошибки в системе. " \
                        f"Купленная работа оставлена вам в подарок"
            )
        else:
            message = f"Ваша заявка на возврат работы id:{ready_task_id}, одобрена. Ожидайте поступление средств."

            send_user_email(
                user=instance.purchase.buyer_transaction.wallet.user,
                subject="Возврат средств!",
                message=f"Ваша заявка на возврат работы id:{ready_task_id}, одобрена. Ожидайте поступление средств."
            )

    if message:
        create_notification(
            user=instance.purchase.buyer_transaction.wallet.user,
            content_type=content_type,
            object_id=instance.id,
            message=message,
            content=content,
            auto_read=auto_read
        )
