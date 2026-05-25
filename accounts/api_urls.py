from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import api_views

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', api_views.RegisterAPIView.as_view(), name='api_register'),
    path('profile/', api_views.ProfileAPIView.as_view(), name='api_profile'),
]