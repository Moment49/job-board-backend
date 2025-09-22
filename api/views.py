from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
# Create your views here.


class UserView(APIView):
    def get(self, request):
        return Response({"message:Hello"})