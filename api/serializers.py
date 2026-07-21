from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Profile, AccountSettings, JobCategory, JobPost, JobApplication, JobApplicationReview
from django.db.models import Q
from django.utils.timezone import now
import uuid
from django.contrib.auth.hashers import check_password

CustomUser = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    # This is to serializeer the User
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', "full_name"]
        read_only_fields = ["id", "full_name", "password"]
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()
    


class RegisterUserSerializer(serializers.ModelSerializer):
    # This is to serializeer the User creation
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'confirm_password', "full_name"]
        read_only_fields = ["id", "full_name", "role"]
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Sorry user with email already exists")
        return value
    
    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError({"error":"Sorry passwords do not match"})
        if len(password) <= 7 and len(confirm_password) <= 7:
            raise serializers.ValidationError({"Password must be greater than 7 characters"})

        return data

    def create(self, validated_data):
        # Create the user
        confirm_password = validated_data.pop('confirm_password')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(email=email, password=password, **validated_data)

            # Add user to Role Group (USER)
            user_group = Group.objects.get(name='User')
            user_group.user_set.add(user)
        
        return user


class AccountVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=555)


class LoginSerialzer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=555)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        user = self.context['request'].user
        # Check that the old password provided matches what is in the database]
        if not check_password(old_password, user.password):
            raise serializers.ValidationError({"error":"Sorry Incorrect old password"})
        # check that the new password is not he old password
        if old_password == new_password:
            raise serializers.ValidationError({"error":"New password must not be the old password"})
        if new_password != confirm_new_password:
            raise serializers.ValidationError({"error":"new Passwords does not match"})
        if len(new_password) <= 7 and len(confirm_new_password) <= 7:
            raise serializers.ValidationError({"error":"Sorry password must be greater than 7 characters"})
        
        return attrs

class AccountSettingDisableSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSettings
        fields = ['settings_id', "is_disabled"]
        read_only_fields = ['settings_id']


class AccountSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSettings
        fields = ['settings_id', "is_disabled", "is_profile_public"]
        read_only_fields = ['settings_id','is_disabled'] 


class ProfileSerializer(serializers.ModelSerializer):
    account_settings = AccountSettingsSerializer(read_only=True)
    bio = serializers.CharField(write_only=True)
    profile_picture = serializers.ImageField(write_only=True)
    get_profile_data = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['profile_id', 'bio', 'interests', 'profile_picture', "get_profile_data", "account_settings"]

    def get_profile_data(self, obj):
        return obj.get_profile_data()
    
    
    def update(self, instance, validated_data):
        profile_pic = validated_data.get('profile_picture', instance.profile_picture)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.interests = validated_data.get('interests', instance.interests)

        if profile_pic:
            # Only update if account_settings allows it
            if instance.account_settings.is_profile_public == False:
                instance.profile_picture = profile_pic
                instance.account_settings.is_profile_public = True
                instance.account_settings.save()

        instance.save()
       
        return instance



"""" THIS IS FOR USER MANAGEMENT BY ADMIN SERIALIZERS """
class AdminUserManagementSerializer(serializers.ModelSerializer):
    # This is to serializer the User creation
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'password', "full_name",  "role"]
        read_only_fields = ["id", "full_name", "role"]
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()

    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Sorry, first name must only contain letters")
        return value
    
    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Sorry, last name must only contain letters")
        return value
    
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email must not be empty")
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Sorry user with email already exists")
        return value
    
    def validate_password(self, value):
        if len(value) < 7:
            raise serializers.ValidationError("Password must be greater than 7 character")
        return value
    
    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")

        # Check if the user exists before creating
        try:
            regular_user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Create the user
            # Set the role to match the human readbale form
            regular_user = CustomUser.objects.create_user(email=email, password=password, **validated_data)
            
            # Activate regular user created by admin
            regular_user.is_active = True
            regular_user.save()

            # Add to the User Role Group
            user_group = Group.objects.get(name='User')
            user_group.user_set.add(regular_user)
        
        return regular_user

    def update(self, instance, validated_data):
        """
        Update and return data
        """
        # Remove/pop password data as password update cannot be done here
        password = validated_data.pop('password', '')

        # Update other data information
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.email = validated_data.get("email", instance.email)

        instance.save()

        return instance


class AdminSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(write_only=True, 
                required=True,
                allow_blank=False,
                error_messages={
                    "required": "First name is required",
                    "blank": "First name cannot be blank"}
                    )
    last_name = serializers.CharField(write_only=True,   
                required=True,
                allow_blank=False,
                error_messages={
                    "required": "last name is required",
                    "blank": "Last name cannot be blank"}
                    )
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'password', "full_name", "role"]
        read_only_fields = ["id", "full_name", 'role']
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()
    
    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Sorry, first name must only contain letters")
        return value
    
    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Sorry, last name must only contain letters")
        return value
    
    def validate_email(self, value):
        if not value.endswith("@admin.com"):
            raise serializers.ValidationError("Email must be a company email (@admin.com)")
        
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Sorry user with email already exists")
        return value
    
    def validate_password(self, value):
        # Validate the password
        if len(value) <= 7:
            raise serializers.ValidationError({"error":"Sorry password must be more than 7 characters"})
        
        return value
    
    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        user = self.context['request'].user

        if user.role != "ADMIN":
            raise serializers.ValidationError({"error":"Sorry role must be an Admin to perform action"})
        try:
            CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_superuser(email=email, password=password, **validated_data)

            # Add user to group ADMIN
            admin_group = Group.objects.get(name="Admin")

            # Add User to group
            admin_group.user_set.add(user)
        return user
    
    def update(self, instance, validated_data):
        # Pop the password when updating the user information
        password = validated_data.pop('password', '')

        # Update other information
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)

        instance.save()

        return instance
        
       
"""" END - THIS IS FOR ADMIN MANAGEMENT SERIALIZERS """

class JobCategorySerializer(serializers.ModelSerializer):
    job_category_name = serializers.CharField(required=True,
                allow_blank=False,
                error_messages={
                    "required": "Job category name is required",
                    "blank": "Job category name cannot be blank"})
    job_category_type = serializers.CharField(required=True,
                allow_blank=False,
                error_messages={
                    "required": "Job category type is required",
                    "blank": "Job category type cannot be blank"})
    class Meta:
        model = JobCategory
        fields = ['job_category_id', 'job_category_name', 'job_category_type']
        read_only_fields = ['job_category_id']

    def validate(self, attrs):
        job_category_type = attrs.get('job_category_type')
        job_category_name = attrs.get('job_category_name')

        if job_category_type not in ['Location', 'Industry', 'Work Type']:
            raise serializers.ValidationError({"error":"Sorry you must select any of these 3 job category Type ('Location', 'Industry', 'Work Type(Remote or Inplace)')"})
     
        # Validate before that job category does not exist
        if JobCategory.objects.filter(job_category_name=job_category_name,
                                        job_category_type=job_category_type).exists():
            raise serializers.ValidationError({"error":"A job category with this name and type already exists."})
        
        return attrs
    
    def create(self, validated_data):
        job_category_name = validated_data.pop('job_category_name')
        job_category_type = validated_data.pop('job_category_type')
        
        job_cat = JobCategory.objects.create(job_category_type=job_category_type, job_category_name=job_category_name)
        job_cat.save()

        return job_cat

    def update(self, instance, validated_data):
        # Update the object instances for the job category
        instance.job_category_name = validated_data.get('job_category_name', instance.job_category_name)
        instance.job_category_type = validated_data.get('job_category_type', instance.job_category_type)
        
        # Save the updated data
        instance.save()

        return instance


class JobPostSerializer(serializers.ModelSerializer):
    job_category = serializers.PrimaryKeyRelatedField(many=True, queryset=JobCategory.objects.all(), required=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    job_title = serializers.CharField(required=True)
    job_description = serializers.CharField(required=True)
    company_name = serializers.CharField(required=True)
    # salary = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)
    class Meta:
        model = JobPost
        fields = ['job_id', 'job_title', 'job_description', 'company_name', 'salary', 'user', 'job_category', 'job_slug']
        read_only_fields = ['job_id', 'job_slug']

    def validate(self, attrs):
        # Check if the category exists or passed to the request
        job_category= attrs.get('job_category')
        
        if not job_category:
            raise serializers.ValidationError({"error":"Please select at least one job category"})
        return attrs 
    
    def create(self, validated_data):
        # The category must be passed in as a list of category ids
        job_catergory_ids = validated_data.pop("job_category")
        job_post = JobPost.objects.create(**validated_data)
        job_post.save()

        # Use set in a m2m relationship so that data can be overwritten and aviod duplicate
        job_post.job_category.set(job_catergory_ids)

        return job_post

    
    def update(self, instance, validated_data):
        # The category must be passed in as a list of category ids
        job_category_ids = validated_data.pop("job_category")

        # Update fields one by one
        instance.job_title = validated_data.pop("job_title", instance.job_title)
        instance.company_name = validated_data.pop("company_name", instance.company_name)
        instance.job_description = validated_data.pop("job_description", instance.job_description)
        instance.salary = validated_data.pop("salary", instance.salary)

        # Update the job post
        instance.save()

        instance.job_category.set(job_category_ids)
        return instance 



class JobApplicationSerializer(serializers.ModelSerializer):
    # job_post =  serializers.PrimaryKeyRelatedField(queryset=JobPost.objects.all())
    user =  serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = JobApplication
        fields = ['job_app_id', 'cover_letter', 'resume_cv',
                  'institution_name', 'field_of_study', 'grade', 'degree_qualification',
                  'degree_start_date', 'degree_end_date', 'degree_certificate', 'availability', 
                  'job_app_submission_status', 'application_review_status', 'user', 'job_post' 
                  ]
        read_only_fields = ['job_app_id', 'job_app_submission_status', 'application_review_status', 'job_post']

    def validate(self, data):
        """Extra validation before create() is called."""

        # Get the current user from the serializer context
        user = self.context['request'].user

    
        # Extract relevant fields from the request data
        start_date = data.get('degree_start_date')
        end_date = data.get('degree_end_date')
        job_post = self.context['job_post']

        # Degree start and end date check
        # Ensure that the end date is not earlier than the start date
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"degree_end_date": "End date cannot be earlier than start date."}
            )

        # Availability date check
        # A candidate cannot set availability to a past date
        availability = data.get('availability')
        if availability and availability < now().date():
            raise serializers.ValidationError(
                {"availability": "Availability date must be today or later."}
            )

        # Prevent multiple submissions for the same job
        # If the user has already submitted a completed application for this job,
        # they cannot apply again.
        existing_application = JobApplication.objects.filter(
            user=user,
            job_post=job_post,
            job_app_submission_status="Submitted"
        )
        if existing_application.exists():
            raise serializers.ValidationError(
                {"error": "You cannot apply for this job again now now"}
            )

        # If all validations pass, return the validated data
        return data
        
    def create(self, validated_data):
        # Get the user who is making the request (from serializer context).
        user = self.context['request'].user

        # Extract the job post the user is applying to.
        # Pop is used here so it's not passed twice into JobApplication.objects.create()
        job_post = self.context['job_post']
      

        # Prevent a user from applying to their own job post.
        if job_post.user == user:
            raise serializers.ValidationError(
                {"job_post": "You cannot apply to a job you created."}
            )

        # Prevent duplicate applications for the same job by the same user
        # if there’s already an *incomplete* application (they should update instead).
        existing_application = JobApplication.objects.filter(
            user=user,
            job_post=job_post,
            job_app_submission_status="Incomplete"
        )
        if existing_application.exists():
            raise serializers.ValidationError(
                {"error": "You already started an application for this job. Please update your previous one instead of creating a new one."}
            )

        # Create a new JobApplication instance with the provided data.
        application = JobApplication.objects.create(
            job_post=job_post,
            **validated_data
        )

        # Run the completeness check (sets status to 'Submitted' if all fields are filled).
        application.check_application_submitted()

        # # Save the instance after the completeness check.
        application.save()

        # Return the newly created application instance.
        return application
    
    def update(self, instance, validated_data):
        # Prevent updates if the job application is already submitted.
        # Business rule: once submitted, users cannot make changes.
        if instance.job_app_submission_status != "Incomplete":
            raise serializers.ValidationError("You have already applied for this job.")

        # Dynamically update only the fields that were provided in validated_data.
        # This way, it supports partial updates (PATCH) without overwriting other fields.
        for key, value in validated_data.items():
            setattr(instance, key, value)

        # Delegate completeness check to the model.
        # This ensures a single source of truth for when an application is considered 'Submitted'.
        instance.check_application_submitted()

        # Save the updated instance after applying changes and recalculating submission status.
        instance.save()

        # Return the updated object back to the serializer.
        return instance


class JobApplicationReviewSerializer(serializers.ModelSerializer):
    reviewed_by =  serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = JobApplicationReview
        fields = ["job_app_review_id", "reason", "reviewed_at", "reviewed_by", "job_applicatiion_review", "job_app"]
        read_only_fields = ['job_app_review_id', 'job_app']

    

    def update(self, instance, validated_data):
        # Update fields normally
        instance.reason = validated_data.get('reason', instance.reason)
        instance.reviewed_at = validated_data.get('reviewed_at', instance.reviewed_at)
        instance.job_applicatiion_review = validated_data.get('job_applicatiion_review', instance.job_applicatiion_review)

        # If review status changes to "Reviewed", mark the application
        if instance.job_applicatiion_review == "Reviewed":
            instance.job_app.application_review_status = True
            instance.job_app.save()

        instance.save()

        return instance
     
