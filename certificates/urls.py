from django.urls import path
from . import views

urlpatterns = [
    path('certificate/', views.certificate_hub_view, name='certificate'),
    path('certificate/<int:cert_id>/', views.certificate_detail_view, name='certificate_detail'),
    path('certificate/<int:cert_id>/delivery/', views.certificate_delivery_view, name='certificate_delivery'),
    path('certificate/<int:cert_id>/pdf/', views.certificate_pdf_view, name='certificate_pdf'),
    path('partners/<int:course_id>/', views.partner_companies_view, name='partner_companies'),
]