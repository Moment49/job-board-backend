from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Profile, AccountSettings, JobCategory, JobPost, JobApplication, JobApplicationReview
from django.db.models import Q

CustomUser = get_user_model()

class RegisterUserSerializer(serializers.ModelSerializer):
    # This is to serializeer the User creation
    user_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['user_id', 'email', 'first_name', 'last_name', 'password', 'confirm_password', "full_name"]
        read_only_fields = ["user_id", "full_name"]
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()
    
    def validate_first_name(self, value):
        if not value:
            raise serializers.ValidationError("First name cannot be empty")
        return value
    
    def validate_last_name(self, value):
        if not value:
            raise serializers.ValidationError("Last name cannot be empty")
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers("Sorry user with email already exists")
        return value


    
    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if not password or not confirm_password:
            raise serializers.ValidationError("Sorry password cannot be empty")
        if password != confirm_password:
            raise serializers.ValidationError("Sorry passwords do not match")
        if len(password) <= 7 or len(confirm_password) <= 7:
            raise serializers.ValidationError("Password must be greater than 7 characters")

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

    def validate(self, data):
        # Check if the data is not empty
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError("Please provide an email")
        if not password:
            raise serializers.ValidationError("Plase provide your password")
        # Return data once validation is complete
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=555)

class AdminUserSerializer(serializers.ModelSerializer):
    # This is to serializeer the User creation
    user_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    role = serializers.CharField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['user_id', 'email', 'first_name', 'last_name', 'password', "full_name",  "role"]
        read_only_fields = ["user_id", "full_name"]
    
    def get_full_name(self, obj):
        # Get the full name of the user from the User obj method
        return obj.get_full_name()
    
    def validate(self, data):
        email = data['email']
        password = data.get('password', '')
        if password:
            if len(password) < 7:
                raise serializers.ValidationError("Password must be greater than 7 character")
        if not email:
            raise serializers.ValidationError("Email must not be empty")
        
        return data
    
    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        # Check if the user exists before creating
        try:
            admin_user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Create the user
            admin_user = CustomUser.objects.create_superuser(email=email, password=password, **validated_data)

            # Add to the admin Role Group
            admin_group = Group.objects.get(name='Admin')
            admin_group.user_set.add(admin_user)
        
        return admin_user

    def update(self, instance, validated_data):
        """
        Update and return and return just your own data
        """
        # Perform role check you cannt change your role once assisgned
        default_role = instance.role
        role_change = validated_data.get("role")
        if default_role != role_change:
            raise serializers.ValidationError("Sorry role changed. Only super Admin can change this")
        else:
            # Check if the user
            instance.first_name = validated_data.get("first_name", instance.first_name)
            instance.last_name = validated_data.get("last_name", instance.last_name)
            instance.email = validated_data.get("first_name", instance.email)

        instance.save()

        return instance


class AccounntSettingDeactivationSerializer(serializers.ModelSerializer):
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
        print(instance.bio)
        if profile_pic:
            # Only update if account_settings allows it
            if instance.account_settings.is_profile_public == False:
                instance.profile_picture = profile_pic
                instance.account_settings.is_profile_public = True
                instance.account_settings.save()

        instance.save()
       
        return instance

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
    
