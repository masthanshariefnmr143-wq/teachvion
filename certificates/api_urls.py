from django.urls import path
from . import api_views

urlpatterns = [
    path('certificates/', api_views.CertificateListAPIView.as_view(), name='api_certificates'),
]