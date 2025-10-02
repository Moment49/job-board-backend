from django.urls import path, include
from .views import (UserRegisterView, 
                    AccountVerificationView, login_view, logout_view, change_password, AdminUserViewSet,
                    ProfileListUpdateView, UserAccountDisableView, JobCategoryViewSet, 
                    JobPostViewSet, JobApplicationViewSet, JobApplicationReviewView, AdminViewSet)

from rest_framework_simplejwt.views import (
    TokenObtainSlidingView,
    TokenRefreshSlidingView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

router = routers.DefaultRouter()

router.register(r'admin/users', AdminUserViewSet, basename="admins-users"),
router.register(r'admin/admins', AdminViewSet, basename="admin-admins"),
router.register(r'categories', JobCategoryViewSet, basename="job-category")
router.register(r'posts', JobPostViewSet)


posts_router = routers.NestedDefaultRouter(router, r"posts", lookup="post")
posts_router.register(r'applications', JobApplicationViewSet, basename="post-applications")


urlpatterns = [
    path('api/token/', TokenObtainSlidingView.as_view(), name='token_obtain'),
    path('api/token/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh'),
    path("auth/register", UserRegisterView.as_view(), name="register"),
    path("auth/account-verification/", AccountVerificationView.as_view(), name="account-verification"),
    path("auth/login", login_view, name="login"),
    path("auth/logout", logout_view, name="logout"),
    path("auth/change-password/<str:user_pk>", change_password, name="change-password"),
    path("profile/", ProfileListUpdateView.as_view(), name="profile"),
    path('profile/<str:user_pk>/disable', UserAccountDisableView.as_view(), name='user-account-disable'),
    path('application/reviews/', JobApplicationReviewView.as_view(), name='application-review'),
    path("", include(posts_router.urls))
]
urlpatterns += router.urls