from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
# Create your views here.


class UserView(APIView):

    def get(self, request):
        # Example usage of send_email function
        context = {"name": "John Though"}
        email_subject = "Welcome to our platform!"

        send_mail(
            subject=email_subject,
            message="Hello, this is a test email from Django.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["ibenachoelvis49@gmail.com"],
            fail_silently=False,
            )
        return Response({"message: " "Email sent successfully!"})