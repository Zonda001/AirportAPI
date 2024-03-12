from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class UserCreateSerializer(serializers.ModelSerializer):
    # Serializer for creating a user
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(label=_("email"), required=True)

    class Meta:
        model = get_user_model()
        fields = ['email', 'password']

    def create(self, validated_data):
        # Create and return a new user instance
        user = get_user_model().objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserSerializer(UserCreateSerializer):
    # Serializer for updating a user
    def update(self, instance, validated_data):
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    # Serializer for authentication token
    email = serializers.CharField(label=_("Email"))
    password = serializers.CharField(
        label=_("Password"), style={"input_type": "password"}
    )

    def validate(self, attrs):
        # Validate user credentials
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    msg = _("User account is disabled.")
                    raise serializers.ValidationError(
                        msg, code="authorization"
                    )
            else:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = _("Must include 'username' and 'password'.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs
