from django.urls import path
from .views import UserRegisterView

urlpatterns = [
    path("auth/register/", UserRegisterView.as_view(), name="register"),
    path("auth/verify/", UserRegisterView.as_view(), name="email-verify"),
]