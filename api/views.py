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
                        LogoutSerializer, AdminUserManagementSerializer, ProfileSerializer,
                        JobCategorySerializer,JobPostSerializer, JobApplicationSerializer,
                        AdminSerializer, ChangePasswordSerializer,JobApplicationReviewSerializer,AccountSettingDisableSerializer)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .tasks import send_verification_email
from django.db import transaction
from rest_framework.decorators import api_view, action
import jwt
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.decorators import permission_classes, authentication_classes
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import Group
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .permissions import IsAdminManagingUsers, AdminReadOnlyForOthers
from .models import Profile, JobApplication, JobApplicationReview, JobCategory, JobPost
import logging
from rest_framework import generics, filters
from django_ratelimit.decorators import ratelimit
from django_filters.rest_framework import DjangoFilterBackend
import uuid
from .filters import JobPostFilter, JobApplicationFilter
from .pagination import JobPostsListsPagination


# Set the logger entry point
logger = logging.getLogger('api.views')

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
            token['user_id'] = str(user.id)
            token['roles'] = user.role

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
      
        return Response({"message":"user created successfully, please check your email for account activation", 
                        "data":serializer.data}, status=status.HTTP_201_CREATED)

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
        except jwt.exceptions.ExpiredSignatureError:
            return Response({"message": "Activation link Expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError:
            return Response({"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Email successfully activated"}, status=status.HTTP_200_OK)

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

@ratelimit(key='user', rate='5/m', block=True)
@ratelimit(key='ip', rate='1/s', block=True)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def change_password(request, user_pk):
    if request.method == "POST":
        # Check that the user making the change is the same user making request
        user = CustomUser.objects.get(id=user_pk)
    
        print(user_pk)
        # Convert to uuid format
        user_pk = uuid.UUID(user_pk)
        print(user_pk)
        if user.pk != user_pk:
            return Response({"error":"Cannot change password of another user"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ChangePasswordSerializer(data=request.data, context={"request":request})
        if serializer.is_valid(raise_exception=True):
            new_password =  serializer.validated_data.get('new_password')
            confirm_new_password = serializer.validated_data.get('confirm_new_password')
            # update the user password that has been validated from the serializer
            if new_password != confirm_new_password:
                raise Response({"error":"Passwords do not match"})
            # change the password for user
            user.set_password(new_password)
            user.save()
            return Response({"detail":f"Password changed for user `{user.get_full_name()}` sucessful"}, status=status.HTTP_200_OK)
        


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



class UserAccountDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request,  *args, **kwargs):
        """
        Disable the account from profile settings.
        Users can disable only their own account.
        """
        # check if user exists
        user_id = kwargs.get('user_pk')
        user_id = uuid.UUID(user_id)
        user = get_object_or_404(CustomUser, id=user_id)

        if not user:
            return Response({"detail": "Missing user id."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure only the logged-in user can disable themselves
        if request.user.id != user_id:
            return Response(
                    {"detail": "You do not have permission to disable other users."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Update account settings
        userprofile = request.user.profile
        account_setting = userprofile.account_settings
        serializer = AccountSettingDisableSerializer(
            account_setting,
            data={"is_disabled":True},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        
        # Deactivate user
        if user.is_active:
            user.is_active = False
            user.save()
            # Blacklist refresh token if provided
            token = serializer.validated_data.get('refresh_token')
            try:
                token = RefreshToken(token)
                token.blacklist()
            except Exception:
                pass

        return Response({"detail": "Account has been disabled successfully."}, status=200)


# ADMIN USER MANAGEMENT
class AdminUserViewSet(ModelViewSet):
    """
    Endpoint: admin/users/

    **Access:** Admin users only.

    Returns all users in the system  for management purposes.
    Supports listing, retrieving, creating, updating, and deleting users.
    """
    # Endpoint to create users by admins 
    permission_classes = [IsAuthenticated, IsAdminManagingUsers]
    authentication_classes = [JWTAuthentication]
    serializer_class = AdminUserManagementSerializer


    @action(detail=True, methods=['post'])
    def disable_user(self, request, pk=None):

        # Check if the user making the request is an ADMIN
        if request.user.role != "ADMIN":
            return Response({"error":"Sorry you can access this resource"})
      
        # Check if the user is valid
        user = get_object_or_404(CustomUser, id=pk)
        if user.is_active:
            # Disable user
            user.profile.account_settings.is_disabled = True
            user.profile.account_settings.save()
            user.is_active = False
            user.save()

            # Blacklist refresh token if provided
            user_tokens = OutstandingToken.objects.filter(user_id=user.id)
            for token in user_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        else:
            return Response({"detail":"Account is already been disabled"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "Account has been disabled successfully."}, status=200)
    
    @action(detail=True, methods=['post'])
    def enable_user(self, request, pk=None):
        user = self.get_object()
        if user.is_active:
            return Response({"detail": "User is already active."}, status=400)
        
        # Re-enable user
        user.is_active = True
        user.profile.account_settings.is_disabled =  False

        # Turn of the is_disable in account settings
        user.profile.account_settings.save()
        user.save()
        return Response({"detail": "Account has been Enable successfully."}, status=200)
    

    def get_queryset(self):
        logger.info("All users returned")
        return CustomUser.objects.filter(role="USER")
    
    def perform_create(self, serializer):
        # Check if the user has the right role before creating
        user = self.request.user
        if user.role != "ADMIN":
            raise PermissionDenied("Sorry you must be an admin to be perform this action")
      
        return serializer.save()
       
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # check if it is a user update
        if instance.role != "USER":
            raise PermissionDenied("Sorry you cannot update data that is not user data")
        
        if instance.role == request.user.role:
            raise PermissionDenied("Sorry you cannot update your data here")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": f"{instance.role} updated successfully", "data":serializer.data}, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"detail": "successfully listed data", "data":serializer.data}, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != "ADMIN":
            raise PermissionDenied({"error":"You cannot view this resource if not an admin"})
        
        if instance.role != "USER":
            raise PermissionDenied({"error": "You cannot view admin users from this endpoint"})
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id == instance.id:
            raise PermissionDenied("Sorry, you cannot delete your own account here.")
        self.perform_destroy(instance)
        return Response({"detail":f"User {instance.get_full_name()} deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    


class AdminViewSet(ModelViewSet):
    """
    Admin View to PERFORM CRUD operations on ADMIN by an Admin
    """
    queryset = CustomUser.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated, AdminReadOnlyForOthers]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail":"Admin created successfully", "data":serializer.data},
                        status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.id  != request.user.id:
            raise PermissionDenied({"error":"You cannot update this resource that is not yours"})
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"detail": f"{instance.role} updated successfully", "data":serializer.data}, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        if request.user.role == "ADMIN":
            queryset = CustomUser.objects.filter(role="ADMIN") 
        else:
            return CustomUser.objects.none()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"detail": "successfully listed data", "data":serializer.data}, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role != "ADMIN":
            raise PermissionDenied({"error":"You cannot view this resource if not an admin"})
        
        if instance.role != "ADMIN":
            raise PermissionDenied({"error": "You cannot view non-admin users from this endpoint"})
        serializer = self.get_serializer(instance)
        return Response(serializer.data)




# JOB CATEGORY MANAGEMNT
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

        return Response({"message":f"category name `{instance.category_name}` updated successfully", "data":serializer.data},status=status.HTTP_200_OK)
    
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
        logger.info(f"Job categories listed successfully :{serializer.data}")
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


# JOB POST MANAGEMENT
class JobPostViewSet(ModelViewSet):
    # View for Job Posts only admins can create update or delete all users can view
    queryset = JobPost.objects.all()
    serializer_class = JobPostSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = JobPostFilter
    pagination_class = JobPostsListsPagination
    search_fields = ['company_name']

    @action(detail=True, methods=['GET'])
    def reviews(self, request, pk=None):
        job_post = self.get_object()
        if request.user.role != "ADMIN" and job_post.user != request.user:
              return Response({"error": "Sorry you cant view this resource"}, status=status.HTTP_403_FORBIDDEN)
        
        reviews = JobApplicationReview.objects.filter(job_app__job_post__user=request.user, 
                                                      job_app__job_post=job_post).select_related('job_app__job_post__user',
                                                                                                 'job_app__job_post')
        serializer = JobApplicationReviewSerializer(reviews, many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


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
        return Response({"message": f"Job post id `{instance.job_id}` updated successfully","data":serializer.data}, status=status.HTTP_200_OK)
    
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
            {"message":f"Job post id `{instance.job.id}` deleted successfully"},
            status=status.HTTP_204_NO_CONTENT)
    
    def list(self, request, *args, **kwargs):
        if request.user.role == "ADMIN":
            job_posts = JobPost.objects.filter(
                user=request.user).prefetch_related('job_category')
        else:
            job_posts = JobPost.objects.prefetch_related('job_category')

        # For Filtering Serach 
        queryset = self.filter_queryset(job_posts) 

        # For Paginated data
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data":serializer.data}, status=status.HTTP_200_OK)


# JOB APPLICATION MANAGEMENT
class JobApplicationViewSet(ModelViewSet):
    # Views for All users to apply to Job Admins/job poster who own the jobs cannot apply to job
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobApplicationFilter
    

    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  
        context['job_post'] =  get_object_or_404(JobPost, pk=self.kwargs['job_post_pk']) 
        return context

    def perform_create(self, serializer):
       print(self.kwargs.get('job_post_pk'))
       serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You cannot delete someone else's application.")
        
        if instance.job_app_submission_status == "Submitted":
            raise PermissionDenied("You cannot delete a submitted application.")

        self.perform_destroy(instance)
        return Response({"message":"application deleted succesfully"},status=status.HTTP_204_NO_CONTENT)
    
    
    def list(self, request, *args, **kwargs):
        # Check if user is admin and is the job poster
        post_id = self.kwargs.get('job_post_pk')
        job_post = get_object_or_404(JobPost, pk=post_id)
        if request.user.role == "ADMIN" and request.user == job_post.user:
           queryset= JobApplication.objects.filter(job_post__user=request.user, job_post=job_post).select_related(
                                              'job_post', 'job_post__user')
        else:
            queryset = JobApplication.objects.filter(user=request.user)

        queryset = self.filter_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# JOB APLLICATION REVIEW MANAGEMENT
class JobApplicationReviewView(APIView):
    permission_classes = [IsAuthenticated]

    # Reviews for Application. Admins to have access to this view only
    def get(self, request, job_app_pk, review_pk):
        if request.user.role != "ADMIN":
            return Response({"message":"Sorry you cant view this resource. Must be an admin"})
        
        job_app = get_object_or_404(JobApplication, job_app_id=job_app_pk)
        
        # Get the specific review
        review = get_object_or_404(JobApplicationReview, job_app_review_id=review_pk, job_app=job_app)
    
        # Serialize the reviews
        serializer = JobApplicationReviewSerializer(review)

        return Response(serializer.data)

    def put(self, request, job_app_pk, review_pk):
       # Only admins can update reviews
        if request.user.role != "ADMIN":
            return Response({"message": "Sorry, you can't update this resource. Must be an admin."},status=403)
        
        job_app = get_object_or_404(JobApplication, job_app_id=job_app_pk)

        review = get_object_or_404(JobApplicationReview, job_app_review_id=review_pk, job_app=job_app)

        # Ensure the admin owns the job post for this application
        if review.job_app.job_post.user != request.user:
            return Response({"error": "You can only update reviews for your own job posts"}, status=403)
        
        # Check if the application has been reviewed already
        if review.job_applicatiion_review == "Reviewed":
            return Response({"message":"Sorry the application has been reviewed already"}, status=status.HTTP_403_FORBIDDEN)

        serializer = JobApplicationReviewSerializer(review, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save(reviewed_by=request.user)

        message = "Review updated successfully"
        if serializer.instance.job_applicatiion_review == "Reviewed":
            message = "Review updated successfully and application marked as reviewed"
            
        return Response({"message": message,"data": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request, job_app_pk, review_pk):
       # Only admins can update reviews
        if request.user.role != "ADMIN":
            return Response({"message": "Sorry, you can't update this resource. Must be an admin."},status=403)
        
        job_app = get_object_or_404(JobApplication, job_app_id=job_app_pk)

        review = get_object_or_404(JobApplicationReview, job_app_review_id=review_pk, job_app=job_app)

        # Ensure the admin owns the job post for this application
        if review.job_app.job_post.user != request.user:
            return Response({"error": "You can only update reviews for your own job posts"}, status=403)
        
        # Check if the application has been reviewed already
        if review.job_applicatiion_review == "Reviewed":
            return Response({"message":"Sorry the application has been reviewed already"}, status=status.HTTP_403_FORBIDDEN)

        serializer = JobApplicationReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(reviewed_by=request.user)

        return Response({"message": "Review updated successfully","data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, job_app_pk, review_pk):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admins can delete this"}, status=403)

        app = get_object_or_404(JobApplication, job_app_id=job_app_pk, job_post__user=request.user)
        review = get_object_or_404(JobApplicationReview, job_app=app, job_app_review_id=review_pk)

        review.delete()
        return Response(status=204)