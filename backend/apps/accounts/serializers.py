from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import serializers

from apps.accounts.models import User
from apps.common.errors import EmailAlreadyRegistered

PASSWORD_MAX_LENGTH = 128  # the minimum is enforced by AUTH_PASSWORD_VALIDATORS


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=PASSWORD_MAX_LENGTH, write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate(self, attrs):  # noqa: ANN001, ANN201
        try:
            password_validation.validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):  # noqa: ANN001, ANN201
        if User.objects.filter(email=validated_data["email"]).exists():
            raise EmailAlreadyRegistered(f"email already registered: {validated_data['email']}")
        try:
            return User.objects.create_user(validated_data["email"], validated_data["password"])
        except IntegrityError as exc:  # lost a race with a concurrent registration
            raise EmailAlreadyRegistered(f"email already registered: {validated_data['email']}") from exc


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=PASSWORD_MAX_LENGTH, write_only=True, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="id")
    role = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="date_joined")

    class Meta:
        model = User
        fields = ["user_id", "email", "role", "created_at"]

    def get_role(self, obj: User) -> str:
        return "admin" if obj.is_staff else "user"


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.ChoiceField(choices=["bearer"])
    expires_in_s = serializers.IntegerField()
