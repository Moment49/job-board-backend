from django.urls import path
from .views import UserRegisterView, AccountVerificationView, login_view, logout_view, AdminUserViewSet
from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'admin', AdminUserViewSet, basename="admin-view")


urlpatterns = [
    path('api/token/', TokenObtainSlidingView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh'),
    path("auth/register", UserRegisterView.as_view(), name="register"),
    path("auth/account-verification/", AccountVerificationView.as_view(), name="account-verification"),
    path("auth/login", login_view, name="login"),
    path("auth/logout", logout_view, name="logout"),
]
urlpatterns += router.urls