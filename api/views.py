from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics
from django.contrib.auth import get_user_model
from .serializers import RegisterUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

CustomUser = get_user_model
# Create your views here.


class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser
    serializer_class = RegisterUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user_data = serializer.data
        user = CustomUser.objects.get(email=user_data['email'])
        # Check ifthe user is active or not
        if not user.is_active:
            # Get the token and send the mail to user
            token = RefreshToken.for_user(user).access_token

            current_site = get_current_site(request).domain
            relativeLink=reverse('email-verify')
            absurl= 'https' if request.is_secure() else 'http'+'://'+current_site+relativeLink+"?token="+token
            email_body = "Hi" + user.get_full_name()
            data = {'domain':absurl}
        
        # Send email using celery tasks
        headers = self.get_success_headers(serializer.data)
        return Response({"message:user created successfully"})

class VerifyEmail(generics.GenericAPIView):
    def get(self):
        ...

