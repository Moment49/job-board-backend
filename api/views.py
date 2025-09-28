from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .serializers import (RegisterUserSerializer, AccountVerificationSerializer, LoginSerialzer, 
                        LogoutSerializer, AdminUserSerializer, ProfileSerializer, AccounntSettingDisableSerializer,
                        JobCategorySerializer,JobPostSerializer, JobApplicationSerializer,JobApplicationReviewSerializer)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .tasks import send_verification_email
from django.db import transaction
from rest_framework.decorators import api_view
import jwt
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework.decorators import permission_classes, authentication_classes
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import Group
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .permissions import IsAdminManagingUsers
from .models import Profile, AccountSettings, JobApplication, JobApplicationReview, JobCategory, JobPost
import logging
from rest_framework import generics, filters
from django_ratelimit.decorators import ratelimit
from django_filters.rest_framework import DjangoFilterBackend


# Set the logger entry point
logger = logging.getLogger(__name__)

CustomUser = get_user_model()


class UserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user_data = serializer.data
        user = CustomUser.objects.get(email=user_data['email'])

        
        # Check if the user active status
        if not user.is_active:
            # Get the token and send the mail to user
            # Add the user role to the token claim
            refresh = RefreshToken.for_user(user)
            token = refresh.access_token  

            # Add custom claims
            # token['roles'] = user.role
            token['user_id'] = str(user.id)

            current_site = get_current_site(request).domain
            relativeLink=reverse('account-verification')
            absurl= ('https' if request.is_secure() else 'http') + '://'+current_site+relativeLink+ "?token=" + str(token)
            email_body = "Hi " + user.get_full_name() +'\nUse the link below to activate your account\n\n'+absurl
            data = {'email_subject':"Verify your email Activation", "email_body":email_body, "to_email":user.email}

            # Send email using celery tasks
            # Ensure that user is created before sending the mail
            try:
                transaction.on_commit(lambda: send_verification_email.delay(data))
            except Exception as e:
                return Response({"message": "Verification task could not be queued. Please try again later.",
                    "error": str(e)}, status=500)
                # Later implement removing the user after sometime if email is not valid will need to implement a web hook for this
      
        return Response({"message:user created successfully"}, status=status.HTTP_201_CREATED)

class AccountVerificationView(APIView):
    serializer_class = AccountVerificationSerializer
    token_param_config = openapi.Parameter('token', in_=openapi.IN_QUERY, description="Token for account verification description", type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        # Get the token from the url
        token = request.GET.get('token')
        # decode the token and get the user claims
        try:
            payload = jwt.decode(token, settings.SECRET_KEY,algorithms=["HS256"])
            user = CustomUser.objects.get(id=payload['user_id'])
            if not user.is_active:
                user.is_active = True
                user.save()
                return Response({"message": "Email successfully activated"}, status=status.HTTP_200_OK)
        except jwt.exceptions.ExpiredSignatureError:
            return Response({"message": "Activation link Expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@ratelimit(key='user', rate='5/m', block=True)
@ratelimit(key='ip', rate='10/m', block=True)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == "POST":
        serializer = LoginSerialzer(data =request.data)
        if serializer.is_valid(raise_exception=True):
            # Get the email and password from request and authenticate user
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(username=email, password=password)
            print(user)
            # Check if user is not None and active
            if user is not None:
                if not user.is_active:
                    # Raise the error for user account not verified 
                    raise AuthenticationFailed('User account not verified. Please check your email for verification link')
                # Check if user account settings is deactivated
                user_profile = Profile.objects.get(user=user)
                if  user_profile.account_settings.is_disabled and user.role == "ADMIN":
                    raise PermissionDenied("Sorry Account disabled. Kindly contact application owner to renable")
                if user_profile.account_settings.is_disabled and user.role != "ADMIN":
                    raise PermissionDenied("Sorry Account disabled. Kindly contact an admin to renable")
    
                # Check the role of the user
                if user.role == "ADMIN":
                    # Create the access and refresh token for user and add the custom claims
                    refresh_token = RefreshToken.for_user(user)
                    access_token = refresh_token.access_token

                    # Add the role of the user will be used to login the user to respective dashboard in the frontend
                    access_token['role'] = user.role
                    # Check if user is a normal User or Admin User based on Role Group
                    return Response({"token": {
                        "access_token":str(access_token),
                        "refresh_token":str(refresh_token)
                    }, "message":"Admin Login successful"}, status=status.HTTP_200_OK)
                elif user.role == "USER":
                    refresh_token = RefreshToken.for_user(user)
                    access_token = refresh_token.access_token
                    # Add the role of the user will be used to login the user to respective dashboard in the frontend
                    access_token['role'] = user.role
                    return Response({"token": {
                        "access_token":str(access_token),
                        "refresh_token":str(refresh_token)
                    }, "message":"User Login successful"}, status=status.HTTP_200_OK)

            return Response({"message":"Invalid Credentials!!! user not authenticated"},status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def logout_view(request):
    if request.method == "POST" and request.user.is_authenticated:
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
             # Blacklist the token and remove then remove the user
            """
            The refresh token associated with the user
            is passed to the body of the request and blacklisted
            """
            token = serializer.validated_data.get('refresh_token')
            token = RefreshToken(token)
            token.blacklist()
            return Response({"message":"Logout successfull"}, status=status.HTTP_200_OK)
        else:
            return  Response({"message":"Bad  request - Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



class AdminUserViewSet(ModelViewSet):
    """
    Endpoint: admin/users/

    **Access:** Admin users only.

    Returns all users in the system (including admins) for management purposes.
    Supports listing, retrieving, creating, updating, and deleting users.
    """
    # Endpoint to create users by admins 
    permission_classes = [IsAuthenticated, IsAdminManagingUsers]
    authentication_classes = [JWTAuthentication]
    serializer_class = AdminUserSerializer

    def perform_create(self, serializer):
        # Check if the user has the right role before creating
        user = self.request.user
        if user.role != "ADMIN":
            return PermissionDenied("Sorry you must be an admin to be perform this action")
        # Admins dont need  to activate accounts for admins
        return serializer.save()

    def get_queryset(self):
        # Check the user role and allow admin to see all users
        return CustomUser.objects.all()
    
    def perform_update(self, serializer):
        serializer.save()
       
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": f"{instance.role} updated successfully", "data":serializer.data}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        if self.request.user.role == 'ADMIN':
            queryset = CustomUser.objects.filter(
                Q(role="USER") | Q(email=self.request.user.email)
            )
        else:
            return CustomUser.objects.none()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail":f"User {instance.get_full_name()} deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    

class ProfileListUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        profile = request.user.profile
        data = request.data.copy()
        # Ensure is_deactivated is never updated
        data.get('account_settings', {}).pop('is_disabled', None)

        serializer = ProfileSerializer(profile, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if request.data.get("profile_picture"):
            detail_msg = "Profile updated successfully with profile picture."
        else:
            detail_msg = "Profile updated successfully without profile picture."

        return Response({
            "detail": detail_msg,
            "profile": serializer.data
        }, status=status.HTTP_200_OK)



class AccountDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request,  *args, **kwargs):
        """
        Disable the account from account settings.
        - Users can deactivate only their own account.
        - Admins can deactivate any account.
        """
        user_id = request.data.get('user_id')
        # check if user exists
        
        if user_id:
            if request.user.role != "ADMIN":
                return Response(
                    {"detail": "You do not have permission to disable other users."},
                    status=status.HTTP_403_FORBIDDEN
                )
            user = get_object_or_404(CustomUser, id=user_id)
            if user.role == "ADMIN":
                return Response(
                    {"detail": "You cannot disable another admin account."},
                    status=status.HTTP_403_FORBIDDEN)
        
       
        # Default: logged-in user's profile
        userprofile = request.user.profile
        account_setting = userprofile.account_settings
        # Call the serializer to update the data
        serializer = AccounntSettingDisableSerializer(
            account_setting,
            data={"is_disabled":True},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Blacklist token if provided
        token = serializer.validated_data.get('refresh_token')
        if token:
            try:
                token = RefreshToken(token)
                token.blacklist()
            except Exception:
                pass
       
        # Once the invalidate there token and them account
        return Response({"detail": "Account has been disabled successfully."}, status=200)

    
class JobCategoryViewSet(ModelViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['job_category_name', 'job_category_type']
    search_fields = ['job_category_type', 'job_category_name']

    def perform_create(self, serializer):
        if self.request.user.role != "ADMIN":
            raise PermissionDenied("Sorry only admins can add categories")
        return serializer.save()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Check if the user is an admin else deny access
        if self.request.user.role != "ADMIN":
            raise PermissionDenied("Sorry only admins can update categories")
        
        self.perform_update(serializer)

        return Response({"message":"category updated successfully", "data":serializer.data},status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if the user is an admin else deny access
        if self.request.user.role != "ADMIN":
            raise PermissionDenied("Sorry only admins can update categories")
        self.perform_destroy(instance)
        return Response({"message":f"category name `{instance.job_category_name}` deleted successfully"},status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class JobPostViewSet(ModelViewSet):
    # View for Job Posts only admins can create update or delete all users can view
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['job_category', 'job_category__job_category_type', 'job_category__job_category_name']
    search_fields = ['company_name', 'salary']

    def perform_create(self, serializer):
        # Check if user is admin before creating
        if self.request.user.role != "ADMIN":
            raise PermissionDenied("Sorry only admins can create job posts")
        return serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Check the user permission
        if request.user.role != "ADMIN":
            return Response({"error": "Sorry you cant update this job post"}, status=status.HTTP_403_FORBIDDEN)
        
        # check if the job post belongs to the person that created it
        if instance.user != request.user:
            return Response({"error": "Sorry you cant update a job post that is not yours job"}, status=status.HTTP_403_FORBIDDEN)

        self.perform_update(serializer)
        return Response({"message": "Job post Updated successfully","data":serializer.data}, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Only admins can delete job posts
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Sorry you cannot delete this job post"}, 
                status=status.HTTP_403_FORBIDDEN)
        
        # Admin cannot delete another admin's post
        if instance.user.role == "ADMIN" and instance.user != request.user:
            return Response(
              {"error": "Admins cannot delete other admins' job posts."}, 
                status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(
            {"message":"Job post deleted successfully"},
            status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        if request.user.role == "ADMIN":
            job_posts = JobPost.objects.filter(
                user=request.user).prefetch_related('job_category')
        else:
            job_posts = JobPost.objects.prefetch_related('job_category')

        # For Filtering Serach 
        queryset = self.filter_queryset(job_posts) 
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


class JobApplicationViewSet(ModelViewSet):
    # Views for All users to apply to Job Admins cannot apply to job
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['application_review_status', 'job_post__job_title']
    search_fields = ['job_application_submission']

    
    def get_seializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  
        return context

    def perform_create(self, serializer):
       serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You cannot delete someone else's application.")
        if instance.job_application_submission == "Submitted":
            raise PermissionDenied("You cannot delete a submitted application.")

        print(instance)
        self.perform_destroy(instance)
        return Response({"message":"application deleted succesfully"},status=status.HTTP_204_NO_CONTENT)
    
    
    def list(self, request, *args, **kwargs):
        # Check if user is admin and is the job poster
        if request.user.role == "ADMIN":
           queryset= JobApplication.objects.filter(job_post__user=request.user, 
                                          job_application_submission_status="Submitted").select_related(
                                              'job_post', 'job_post__user')
        else:
            queryset = JobApplication.objects.filter(user=request.user)

        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class JobApplicationReviewView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['job_applicatiion_review', 'reviewed_at', "job_app__field_of_study"]

    # Reviews for Application. Admins to have access to this view only
    def get(self, request):
        if request.user.role != "ADMIN":
            return Response({"message":"Sorry you cant view this resource. Must be an admin"})
        
         # Get all JobApplicationReviews for applications of jobs posted by this admin
        reviews = JobApplicationReview.objects.filter(
            job_app__job_post__user=request.user
        ).select_related('job_app', 'job_app__job_post', 'reviewed_by')

        # Serialize the reviews
        serializer = JobApplicationReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def put(self, request):
       # Only admins can update reviews
        if request.user.role != "ADMIN":
            return Response(
                {"message": "Sorry, you can't update this resource. Must be an admin."},
                status=403
            )
        
        review_id = request.data.get('job_app_review_id')
        if not review_id:
            return Response({"error": "review_id is required"}, status=400)

        try:
            review = JobApplicationReview.objects.get(job_app_review_id=review_id)
        except JobApplicationReview.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

        # Ensure the admin is the owner of the related job post
        if review.job_app.job_post.user != request.user:
            return Response({"error": "You can only update reviews for your own job posts"}, status=403)

        serializer = JobApplicationReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)