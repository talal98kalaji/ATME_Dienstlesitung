from rest_framework import serializers


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
    )

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class NewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    def validate(self, data):
        if (
            data["new_password"]
            != data["password_confirm"]
        ):
            raise serializers.ValidationError({
                "password_confirm":
                    "Passwords do not match.",
            })

        return data


class PasswordChangeSerializer(NewPasswordSerializer):
    old_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class ResetConfirmSerializer(NewPasswordSerializer):
    user = serializers.IntegerField(
        min_value=1,
    )

    token = serializers.CharField(
        write_only=True,
        max_length=256,
        trim_whitespace=False,
    )