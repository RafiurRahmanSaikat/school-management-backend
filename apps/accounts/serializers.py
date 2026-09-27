from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "uuid",
            "username",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "gender",
            "date_of_birth",
            "profile_picture",
            "address_line",
            "city",
            "district",
            "post_code",
            "country",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "uuid", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "gender",
            "date_of_birth",
            "address_line",
            "city",
            "district",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
