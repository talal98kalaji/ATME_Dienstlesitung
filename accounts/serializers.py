from django.contrib.auth import get_user_model
from .password_validation import validate_api_password
from .password_services import login_payload
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .permissions import is_manager, is_superuser


User = get_user_model()


def validate_account_authority(serializer, data):
    request = serializer.context.get('request')
    actor = getattr(request, 'user', None)

    if not is_manager(actor):
        raise PermissionDenied(
            'Only a superuser or manager can manage accounts.'
        )
    instance = serializer.instance
    if (
        instance is not None
        and instance.is_superuser
        and not is_superuser(actor)
    ):
        raise PermissionDenied(
            'Only a superuser can modify a superuser account.'
        )
    next_superuser = data.get(
        'is_superuser',
        getattr(instance, 'is_superuser', False)
    )

    if next_superuser and not is_superuser(actor):
        raise PermissionDenied(
            'Only a superuser can grant superuser status.'
        )

    previous_type = getattr(instance, 'user_type', None)

    next_type = data.get(
        'user_type',
        previous_type
    )

    if (
        next_type == 'MANAGER'
        and previous_type != 'MANAGER'
        and not is_superuser(actor)
    ):
        raise PermissionDenied(
            'Only a superuser can create or promote a manager.'
        )

    if next_type == 'MANAGER' and next_superuser:
        raise serializers.ValidationError({
            'is_superuser':
                'A manager account cannot also be a superuser.'
        })

    if next_superuser:
        data['is_staff'] = True

    if next_type == 'DATA_ENTRY' and not next_superuser:
        if data.get('is_staff'):
            raise serializers.ValidationError({
                'is_staff':
                    'Data-entry accounts cannot access Django administration.'
            })

        data['is_staff'] = False

    return data


class AccountsSerializers(serializers.ModelSerializer):
    user_type_display = serializers.CharField(
        source='get_user_type_display',
        read_only=True
    )

    level_display = serializers.CharField(
        source='get_level_display',
        read_only=True
    )

    class Meta:
        model = User
        exclude = ['password']


class EmployeeCreateSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
        style={"input_type": "password"},
        label="Verify your password",
    )

    class Meta:
        model = User
        extra_kwargs = {"password": {"write_only": True,"trim_whitespace": False,
                        "max_length": 128,"style": {"input_type": "password",},},}
        fields = [
            'username',
            'password',
            'password_confirm',
            'email',
            'first_name',
            'last_name',
            'user_type',
            'level',
            'phone_number',
            'street',
            'post_number',
            'house_number',
            'details',
            'image',
            'is_active',
            'is_staff',
            'is_superuser',
        ]

        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'}
            }
        }

    def validate(self, data):
        data = validate_account_authority(self, data)

        password = data.get('password')
        password_confirm = data.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })

        candidate = User(
            username=data.get("username", ""),
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )

        validate_api_password(
            password,
            candidate,
        )

        username = data.get('username')

        if username and User.objects.filter(
            username=username
        ).exists():
            raise serializers.ValidationError({
                'username': 'This username is already taken.'
            })

        email = data.get('email')

        if email and User.objects.filter(
            email=email
        ).exists():
            raise serializers.ValidationError({
                'email': 'This email is already used.'
            })

        phone_number = data.get('phone_number')

        if phone_number and User.objects.filter(
            phone_number=phone_number
        ).exists():
            raise serializers.ValidationError({
                'phone_number': 'This number is already used.'
            })

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
            'username',
            'email',
            'first_name',
            'last_name',
            'user_type',
            'level',
            'phone_number',
            'street',
            'post_number',
            'house_number',
            'details',
            'image',
            'is_active',
            'is_staff',
            'is_superuser',
        ]

    def validate(self, data):
        return validate_account_authority(self, data)


class CustomLoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        return login_payload(
            attrs["username"],
            attrs["password"],
            request=self.context.get("request"),
        )