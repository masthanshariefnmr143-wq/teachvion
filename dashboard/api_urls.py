from django.urls import path
from . import api_views

urlpatterns = [
    path('dashboard/summary/', api_views.DashboardSummaryAPIView.as_view(), name='api_dashboard_summary'),
]