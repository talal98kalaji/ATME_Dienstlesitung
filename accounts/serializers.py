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
                {"password": "password not match , check theme then try again"}
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