from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework import serializers


class NumberAndSymbolValidator:
    def validate(self, password, user=None):
        errors = []

        if not any(
            character.isdecimal()
            for character in password
        ):
            errors.append(
                "Password must contain a number."
            )

        if not any(
            not character.isalnum()
            and not character.isspace()
            for character in password
        ):
            errors.append(
                "Password must contain a symbol such as ! @ # $."
            )

        if len(password) > 128:
            errors.append(
                "Password must not exceed 128 characters."
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "Include a number and a symbol; "
            "maximum length is 128 characters."
        )


def validate_api_password(password, user):
    try:
        validate_password(
            password,
            user=user,
        )

    except ValidationError as exc:
        raise serializers.ValidationError({
            "password": exc.messages,
        })