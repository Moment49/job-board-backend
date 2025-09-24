from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

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
        if len(password) <= 7 or len(confirm_password):
            raise serializers.ValidationError("Password must be greater than 7 characters")

        return data


    def create(self, **validated_data):
        # Create the user
        confirm_password = validated_data.pop('confirm_password')
        email = validated_data.pop('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = CustomUser.objects.create_user(email=email, **validated_data)

            # Add user to Role Group (USER)
            user_group = Group.objects.get(name='User')
            user_group.user_set.add(user)
        
        return user


class LoginSerialzer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)