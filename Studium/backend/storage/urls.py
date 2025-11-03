from django.urls import path
from .views import *

urlpatterns = [
    path('load/', TempStorageUploadFileView.as_view()),
    path('upd_links/', StartUpdateFileTemporaryLinksView.as_view()),
    path('upd_links_check/', CeleryUpdateLinksStatusView.as_view()),
    path('archive/<int:pk>/download/', ArchiveDownloadView.as_view(), name='archive-download'),
    path('archive/<int:pk>/download_public/', PublicFileDownloadView.as_view(), name='archive-download-public'),
]
