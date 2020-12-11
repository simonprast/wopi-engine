#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import serializers

from user.models import User

from user.create_or_login import validated_user_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'is_admin']


class UserDetailSerializer(serializers.Serializer):
    first_name, last_name, email, phone, password = None, None, None, None, None

    def validate(self, value):
        # Ensure that the given user arguments are valid and set the values accordingly
        self.first_name, self.last_name, self.email, self.phone, self.password = validated_user_data(
            self.initial_data)
        return value

    def save(self):
        user = User.objects.create_user(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            password=self.password,
            serializers=serializers
        )

        return True if user else False


class LoginUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ChangeUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone'
        ]
