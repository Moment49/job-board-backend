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
    # This is to serializeer the User creation
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
            # Add to the admin Role Group
            admin_group = Group.objects.get(name='User')
            admin_group.user_set.add(regular_user)
        
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
    class Meta:
        model = JobCategory
        fields = ['job_category_id', 'job_category_name', 'job_category_type']
        read_only_fields = ['job_category_id']

    def validate(self, data):
        job_category_type = data.get('job_category_type')
        job_category_name = data.get('job_category_name')

        if job_category_type not in ['Location', 'Industry', 'Type']:
            raise serializers.ValidationError("Sorry you must select any of these 3 Job category Type ('Location', 'Industry', 'Type')")
        if not job_category_name:
            raise serializers.ValidationError("Sorry Job category name cannot be empty")
        
        return data
    
    def create(self, validated_data):
        job_category_name = validated_data.pop('job_category_name')
        job_category_type = validated_data.pop('job_category_type')
    
        job_cat = JobCategory.objects.filter(job_category_name=job_category_name, job_category_type=job_category_type)
        if job_cat.exists():
            raise serializers.ValidationError("A job category with this name and type already exists.")
        
        job_cat = JobCategory.objects.create(job_category_type=job_category_type, job_category_name=job_category_name)
        
        job_cat.save()
        return job_cat

    def update(self, instance, validated_data):
        instance.job_category_name = validated_data.get('job_category_name', instance.job_category_name)
        instance.job_category_type = validated_data.get('job_category_type', instance.job_category_type)

        instance.save()
        return instance

class UUIDWithoutDashField(serializers.UUIDField):
    def to_internal_value(self, data):
        try:
            # Add dashes if missing
            if isinstance(data, str) and "-" not in data:
                data = str(uuid.UUID(data))
            return super().to_internal_value(data)
        except ValueError:
            self.fail("invalid", value=data)


class JobPostSerializer(serializers.ModelSerializer):
    job_category = serializers.PrimaryKeyRelatedField(many=True, queryset=JobCategory.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = JobPost
        fields = ['job_id', 'job_title', 'job_description', 'company_name', 'salary', 'user', 'job_category']
        read_only_fields = ['job_id']

    
    def validate(self, data):
        job_title = data.get('job_title')
        job_desc = data.get('job_description')
        job_company = data.get('company_name')
        job_salary = data.get('salary')
        if not job_title:
            raise serializers.ValidationError("Job title must not be empty")
        if not job_company:
            raise serializers.ValidationError("Company must not be empty")
        if not job_desc:
            raise serializers.ValidationError("Job description must not be empty")
        if not job_salary:
            raise serializers.ValidationError("Job salary must not be empty")
        
        return data

    
    def create(self, validated_data):
        job_catergory_ids = validated_data.pop("job_category")
        # Create the job post
        job_post = JobPost.objects.create(**validated_data)
        job_post.save()

        job_post.job_category.set(job_catergory_ids)

        return job_post


    
    def update(self, instance, validated_data):
        job_category_ids = validated_data.pop("job_category")

        # Update fields one by one
        instance.job_title = validated_data.pop("job_title", instance.job_title)
        instance.company_name = validated_data.pop("company_name", instance.company_name)
        instance.job_description = validated_data.pop("job_description", instance.job_description)
        instance.salary = validated_data.pop("salary", instance.salary)

       
        instance.save()

        instance.job_category.set(job_category_ids)
        return instance 


class JobApplicationSerializer(serializers.ModelSerializer):
    job_post =  serializers.PrimaryKeyRelatedField(queryset=JobPost.objects.all())
    user =  serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = JobApplication
        fields = ['job_app_id', 'cover_letter', 'resume_cv',
                  'institution_name', 'field_of_study', 'grade', 'degree_Qualification',
                  'degree_start_date', 'deree_end_date', 'degree_Certificate', 'availability', 
                  'job_application_submission', 'application_review_status', 'user', 'job_post' 
                  ]
        read_only_fields = ['job_app_id', 'job_application_submission', 'application_review_status']

    def validate(self, data):
        """Extra validation before create() is called"""
        # Dates check
        user = self.context['request'].user
        start_date = data.get('degree_start_date')
        end_date = data.get('degree_end_date')
        job_post = data.get('job_post')
      

        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"degree_end_date": "End date cannot be earlier than start date."}
            )

        # Availability date check
        availability = data.get('availability')
        if availability and availability < now().date():
            raise serializers.ValidationError(
                {"availability": "Availability date must be today or later."}
            )
            
        # Check that user has not applied for job before
        # print(job_post)
        existing_application = JobApplication.objects.filter(
            user=user,
            job_post=job_post,
            job_application_submission="Submitted"
        )
        if existing_application.exists():
            raise serializers.ValidationError({"error": "You cannot apply for this job again"})
        
        return data
        
    def create(self, validated_data):
        # Get the user making the request
        user = self.context['request'].user

        # Get the job post the user is applying to
        job_post = validated_data.pop('job_post')

        # List of all fields required to consider the application complete
        all_fields =['cover_letter', 'resume_cv',
                  'institution_name', 'field_of_study', 'grade', 'degree_Qualification',
                  'degree_start_date', 'deree_end_date', 'degree_Certificate', 'availability', 
                  ]
        
        # Prevent a user from applying to a job they created themselves
        if job_post.user == user:
            raise serializers.ValidationError(
                {"job_post": "You cannot apply to a job you created."})
    

        existing_application = JobApplication.objects.filter(
            user=user,
            job_post=job_post,
            job_application_submission="Incomplete"
        )
        if existing_application.exists():
            raise serializers.ValidationError(
                {"error": "You cannot create a new application please update your former on for this job again"})
        # Check if all required fields are filled
        filled_data = all(validated_data.get(field) for field in all_fields)
        
        # Determine submission status based on whether all fields are filled
        validated_data['job_application_submission'] = "Submitted" if filled_data else "Incomplete"
        
        # Create the JobApplication object in the database   
        application = JobApplication.objects.create( job_post=job_post, **validated_data)   

        application.save()
        
        return application
    
    def update(self, instance, validated_data):
        # Check the current submission status
        submition_status = instance.job_application_submission 

        # Only allow updating if the application is still incomplete
        if submition_status != "Incomplete":
            raise serializers.ValidationError("You have applied for this job")
        
        # Update instance fields dynamically from validated_data
        for key, value in validated_data.items():
            setattr(instance, key, value)
        # List of all fields required for a complete application
        all_fields = ['cover_letter', 'resume_cv',
                  'institution_name', 'field_of_study', 'grade', 'degree_Qualification',
                  'degree_start_date', 'deree_end_date', 'degree_Certificate', 'availability', 
                  ]
      
        filled_data = all(getattr(instance, field) for field in all_fields)
        instance.job_application_submission = "Submitted" if filled_data else "Incomplete" 
        
        instance.save()
        return instance

class JobApplicationReviewSerializer(serializers.ModelSerializer):
    job_app =  serializers.PrimaryKeyRelatedField(queryset=JobPost.objects.all())
    reviewed_by =  serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = JobApplicationReview
        fields = ["job_app_review_id", "reason", "reviewed_at", "reviewed_by", "job_applicatiion_review", "job_app"]
        read_only_fields = ['job_app_review_id']

    def update(self, instance, validated_data):
        # check if the application is submitted if it is then review it
        reviewed_by = validated_data.get('reviewed_by')
        instance.reason = validated_data.get('reason', instance.reason)
        instance.reviewed_at = validated_data.get('reviewed_at', instance.reviewed_at)
        instance.reviewed_by = validated_data.get('reviewed_by', instance.reviewed_by)

        instance.job_applicatiion_review = validated_data.get('job_applicatiion_review', instance.job_applicatiion_review)
    
        if instance.job_applicatiion_review == "Reviewed":
            # Update the application_review_status of the job application
            instance.job_app.application_review_status = True
        instance.save()

        return instance
     
