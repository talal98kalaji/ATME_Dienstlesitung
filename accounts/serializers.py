from .models import CustomUser
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class AccountsSerializers(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    class Meta:
        model = User
        exclude = ['password']



class EmployeeCreateSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'},
        label="verify your password"
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'password_confirm', 'email', 'first_name', 'last_name',
            'user_type', 'level', 'phone_number', 'street', 
            'post_number', 'house_number', 'details', 'image',
            'is_active', 'is_staff'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def validate(self, data):
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        if password != password_confirm:
            raise serializers.ValidationError(
                {"password": "Password does not match, check them then try again."}
            )
        

        username = data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                {"username": "this username is already taken"}
            )

        email = data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "this email is already used"}
            )

        phone_number = data.get('phone_number')
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError(
                {"phone_number": "this number is already used"}
            )

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')        
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'user_type', 'level', 'phone_number', 'street', 
            'post_number', 'house_number', 'details', 'image',
            'is_active', 'is_staff'
        ]

class CustomLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'user_type': self.user.user_type,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_superuser': self.user.is_superuser,
            'is_active': self.user.is_active
        }
        
        return data