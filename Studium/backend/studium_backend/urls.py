from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('stranger/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/up/', include('users.urls')),
    path('api/rt/', include('ready_tasks.urls')),
    path('api/ot/', include('order_tasks.urls')),
    path('api/ts/', include('storage.urls')),
    path('api/re/', include('reports.urls')),
    path('api/rate/', include('feedbacks.urls')),
    path('api/jsons/', include('jsons.urls')),
    path('api/rules/', include('rules.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/refund/', include('refunds.urls')),
]
