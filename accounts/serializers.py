from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={"invalid": "invalid_email_format"}
    )
    password = serializers.CharField(write_only=True)
    nickname = serializers.CharField()
    gender = serializers.ChoiceField(choices=User.GENDER_CHOICES)
    age = serializers.IntegerField(min_value=1, max_value=120)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("email_already_exists")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("invalid_password_format")
        return value

    def validate_nickname(self, value):
        if not (2 <= len(value) <= 10):
            raise serializers.ValidationError("invalid_nickname_length")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("invalid_credentials")
        attrs["user"] = user
        return attrs


class MyPageSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["nickname", "gender", "email"]