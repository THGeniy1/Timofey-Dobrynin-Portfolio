from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Client, CustomUser

from reports.models import Report, ReportComment, Files as ReportFiles
from feedbacks.models import Feedback
from ready_tasks.models import ReadyTask, Files as TaskFiles, PlacementPackage
from payments.models import PurchasedReadyTask, FrozenFunds, Wallet, SlotsPurchase
from users.models import Education
from notifications.models import Notification, FailureNotification
from jsons.models import JsonFile
from rules.models import Rules


def create_client_group(sender=None, **kwargs):
    group, created = Group.objects.get_or_create(name='Client')

    ct_custom_user = ContentType.objects.get_for_model(CustomUser)
    custom_user_perms = Permission.objects.filter(
        content_type=ct_custom_user,
        codename__in=['view_customuser', 'change_customuser']
    )

    ct_client = ContentType.objects.get_for_model(Client)
    client_perms = Permission.objects.filter(
        content_type=ct_client,
        codename__in=['view_client', 'change_client', 'add_client']
    )

    ct_education = ContentType.objects.get_for_model(Education)
    education_perms = Permission.objects.filter(
        content_type=ct_education,
        codename__in=['view_education', 'change_education', 'delete_education']
    )

    ct_ready_task = ContentType.objects.get_for_model(ReadyTask)
    ready_task_perms = Permission.objects.filter(
        content_type=ct_ready_task,
        codename__in=['view_readytask', 'add_readytask', 'change_readytask']
    )

    ct_task_files = ContentType.objects.get_for_model(TaskFiles)
    task_files_perms = Permission.objects.filter(
        content_type=ct_task_files,
        codename__in=['view_files', 'add_files', 'change_files']
    )

    ct_purchased_task = ContentType.objects.get_for_model(PurchasedReadyTask)
    purchased_task_perms = Permission.objects.filter(
        content_type=ct_purchased_task,
        codename__in=['view_purchasedreadytask', 'add_purchasedreadytask']
    )

    ct_feedback = ContentType.objects.get_for_model(Feedback)
    feedback_perms = Permission.objects.filter(
        content_type=ct_feedback,
        codename__in=['add_feedback', 'view_feedback']
    )

    ct_report = ContentType.objects.get_for_model(Report)
    report_perms = Permission.objects.filter(
        content_type=ct_report,
        codename__in=['add_report']
    )

    ct_report_comment = ContentType.objects.get_for_model(ReportComment)
    report_comment_perms = Permission.objects.filter(
        content_type=ct_report_comment,
        codename__in=['add_reportcomment']
    )

    ct_report_files = ContentType.objects.get_for_model(ReportFiles)
    report_files_perms = Permission.objects.filter(
        content_type=ct_report_files,
        codename__in=['add_files']
    )

    ct_notification = ContentType.objects.get_for_model(Notification)
    notification_perms = Permission.objects.filter(
        content_type=ct_notification,
        codename__in=['view_notification']
    )

    ct_failure_notification = ContentType.objects.get_for_model(FailureNotification)
    failure_notification_perms = Permission.objects.filter(
        content_type=ct_failure_notification,
        codename__in=['view_failure_notification']
    )

    ct_json_file = ContentType.objects.get_for_model(JsonFile)
    json_file_perms = Permission.objects.filter(
        content_type=ct_json_file,
        codename__in=[]
    )

    ct_rules = ContentType.objects.get_for_model(Rules)
    rules_perms = Permission.objects.filter(
        content_type=ct_rules,
        codename__in=[]
    )

    ct_frozen_funds = ContentType.objects.get_for_model(FrozenFunds)
    frozen_funds_perms = Permission.objects.filter(
        content_type=ct_frozen_funds,
        codename__in=['view_frozenfunds']
    )

    ct_wallet = ContentType.objects.get_for_model(Wallet)
    wallet_perms = Permission.objects.filter(
        content_type=ct_wallet,
        codename__in=['view_wallet']
    )

    ct_placement_package = ContentType.objects.get_for_model(PlacementPackage)
    placement_package_perms = Permission.objects.filter(
        content_type=ct_placement_package,
        codename__in=['view_placementpackage']
    )

    ct_slots_purchase = ContentType.objects.get_for_model(SlotsPurchase)
    slots_purchase_perms = Permission.objects.filter(
        content_type=ct_slots_purchase,
        codename__in=['view_slotspurchase']
    )

    all_perms = list(custom_user_perms) + list(client_perms) + list(education_perms) + \
                list(ready_task_perms) + list(task_files_perms) + list(purchased_task_perms) + \
                list(feedback_perms) + list(report_perms) + list(report_comment_perms) + \
                list(report_files_perms) + list(notification_perms) + list(failure_notification_perms) + \
                list(json_file_perms) + list(rules_perms) + list(frozen_funds_perms) + \
                list(wallet_perms) + list(placement_package_perms) + list(slots_purchase_perms)

    group.permissions.set(all_perms)
