from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import uuid
from django.conf import settings
# Create your models here.
import logging
import os


# This gets the full file path to where we can log the requests
full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs/models.log'))
# Set up logging
logging.basicConfig(filename=full_path,
                    format='%(asctime)s %(message)s',
                    filemode='a')

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name=None, last_name=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        
        if not first_name:
            raise ValueError("First name is required")
        
        if not last_name:
            raise ValueError("Last name is required")
        
        if not password:
            raise ValueError("Password is required")

        # Normalize the email address by lowercasing the domain part of it.
        user = self.model(email=self.normalize_email(email), 
                          first_name=first_name,
                          last_name=last_name,
                           **extra_fields)
        
        # Hash the password using the default password hasher
        user.set_password(password)
        user.is_active = False
        user.save(using=self._db)

        return user
    
    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        # Set the user role to admin
        extra_fields['role'] = "ADMIN"
        
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)

        return user



class CustomUser(AbstractUser):

    ROLES = (
        ("ADMIN", "Admin"),
        ("USER", "User"),
    )

    # Add any additional fields if needed
    id = models.UUIDField(primary_key=True,  default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    email = models.EmailField(unique=True, blank=False, null=False)
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLES, default="USER")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        ordering = ['-created_at', 'role']

    def get_full_name(self):
        """This will get the full name of the user"""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.email}"

class AccountSettings(models.Model):
    settings_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_disabled = models.BooleanField(default=False)
    is_profile_public = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings {self.settings_id}"

class Profile(models.Model):
    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile/', blank=True, null=True)
    interests = models.CharField(max_length=200, blank=True, null=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_settings = models.OneToOneField(AccountSettings, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_profile_data(self):
        # Get the profile data to be displayed and user for updating  ser data
        profile_data = { "first_name":self.user.first_name, 
                            "last_name": self.user.last_name,
                            "email":self.user.email,
                            "bio": self.bio,
                            "interests":self.interests,
                            "profile_picture":self.profile_picture.url if self.profile_picture else None}
        return profile_data


    def __str__(self):
        return f"Profile of {self.user.email}"
    

class JobCategory(models.Model):
    JOB_CATEGORY_TYPES = [
    ("Location", "Location"),
    ("Work Type", "Work Type"),
    ("Industry", "Industry")
    ]
    job_category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_category_name = models.CharField(max_length=45, blank=True, null=True)
    job_category_type = models.CharField(max_length=20, choices=JOB_CATEGORY_TYPES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_category_id}"

class JobPost(models.Model):
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=100, blank=False, null=False)
    job_description = models.TextField(blank=False, null=False)
    company_name = models.CharField(max_length=100, blank=False, null=False)
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_posts')
    job_category = models.ManyToManyField(JobCategory, related_name="job_posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"

class JobApplication(models.Model):
    JOB_APPLICATION_SUBMISSION_STATUS = [
    ("Submitted", "Submitted"),
    ("Incomplete", "Incomplete"),
    ]
    job_app_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cover_letter = models.TextField(blank=True, null=True)
    resume_cv = models.FileField(upload_to="resume/", blank=True, null=True)
    institution_name = models.CharField(max_length=100, blank=True, null=True)
    field_of_study = models.CharField(max_length=100, blank=True, null=True)
    grade = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    degree_qualification = models.CharField(max_length=200, blank=True, null=True)
    degree_start_date = models.DateField(blank=True, null=True)
    degree_end_date  = models.DateField(blank=True, null=True)
    degree_certificate = models.ImageField(upload_to="certificates/", blank=True, null=True)
    availability = models.DateField(blank=True, null=True)
    job_app_submission_status = models.CharField(max_length=15, choices=JOB_APPLICATION_SUBMISSION_STATUS, default="Incomplete", blank=True, null=True)
    application_review_status = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    job_post = models.ForeignKey(JobPost, on_delete=models.SET_NULL, related_name="job_applications", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_app_id} at {self.user.email}"


    def check_application_submitted(self):
        # Get all fields
        submission_fields = [self.cover_letter,
                    self.resume_cv, self.field_of_study,
                    self.grade, self.institution_name,
                    self.degree_certificate, self.degree_start_date,
                    self.degree_end_date, self.availability]
        
        # Check if all the values of the fields are filled
        if all(field is not None and field != "" for field in submission_fields):
            self.job_app_submission_status = "Submitted"
            logger.info(f"Fields are all filled. marked Submitted")
        else:
            self.job_app_submission_status = 'Incomplete'
            logger.info(f"Fields are not all filled. marked Incomplete")


        


class JobApplicationReview(models.Model):
    JOB_APPLICATION_REVIEW_STATUS = [
            ("Reviewed", "Reviewed"),
            ("Not Reviewed", "Not Reviewed"),
            ]
    
    job_app_review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reason = models.TextField(blank=False, null=False)
    reviewed_at = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="job_application_review", null=True)
    job_applicatiion_review = models.CharField(max_length=20, choices=JOB_APPLICATION_REVIEW_STATUS, default="Not Reviewed", blank=False, null=False)
    job_app = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name="job_application_reviews")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.job_app_review_id} for job application {self.job_app.job_app_id}"
    

class RequestLog(models.Model):
    ip_address = models.CharField(max_length=45)
    path = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.ip_address} - {self.path} at {self.timestamp} from {self.city}, {self.country}"



