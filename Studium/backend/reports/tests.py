from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from authentication.models import CustomUser
from .models import Report, ReportComment


class ReportModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="user@example.com", password="pass")

    def test_report_str_contains_id(self):
        report = Report.objects.create(user=self.user, reported_user=self.user, type="report")
        self.assertIn(str(report.id), str(report))

    def test_report_comment_str_contains_report_id(self):
        report = Report.objects.create(user=self.user, reported_user=self.user, type="report")
        comment = ReportComment.objects.create(report=report, user=self.user, comment="text")
        self.assertIn(str(report.id), str(comment))
