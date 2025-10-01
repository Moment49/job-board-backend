from django.urls import path
from .views import (UserRegisterView, 
                    AccountVerificationView, login_view, logout_view, change_password, AdminUserViewSet,
                    ProfileListUpdateView, UserAccountDisableView, JobCategoryViewSet, 
                    JobPostViewSet, JobApplicationViewSet, JobApplicationReviewView, AdminViewSet)

from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'admin/users', AdminUserViewSet, basename="admins-users"),
router.register(r'admin/admins', AdminViewSet, basename="admin-admins"),
router.register(r'job/category', JobCategoryViewSet, basename="job-category")
router.register(r'job-posts', JobPostViewSet, basename="job-posts")
router.register(r'job-applications', JobApplicationViewSet, basename="job-applications")



urlpatterns = [
    path('api/token/', TokenObtainSlidingView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh'),
    path("auth/register", UserRegisterView.as_view(), name="register"),
    path("auth/account-verification/", AccountVerificationView.as_view(), name="account-verification"),
    path("auth/login", login_view, name="login"),
    path("auth/logout", logout_view, name="logout"),
    path("auth/change-password/<str:user_pk>", change_password, name="change-password"),
    path("profile/", ProfileListUpdateView.as_view(), name="profile"),
    path('profile/<str:user_pk>/disable', UserAccountDisableView.as_view(), name='account-disable'),
    path('application/reviews/', JobApplicationReviewView.as_view(), name='application-review'),

]
urlpatterns += router.urls