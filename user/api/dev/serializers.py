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
    advisor = serializers.UUIDField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    def validate(self, value):
        # If the request method is PUT it must be stated that the object
        # is only changed and the fields will therefore only be optional.
        change = True if self.context.get('request').method == 'PUT' else False

        # Ensure that the given user arguments are valid and set the values accordingly
        self.first_name, self.last_name, self.email, self.phone, self.password = validated_user_data(
            self.initial_data, change=change)
        return value

    def update(self, instance, validated_data):
        instance.first_name = self.first_name or instance.first_name
        instance.last_name = self.last_name or instance.last_name
        instance.email = self.email or instance.email
        instance.phone = self.phone or instance.phone

        new_password = False
        if not instance.check_password(self.password):
            instance.set_password(self.password)
            new_password = True

        if self.initial_data.get('advisor'):
            try:
                advisor = User.objects.get(
                    pk=self.initial_data.get('advisor'), utype=7)
                instance.advisor = advisor
            except User.DoesNotExist:
                return "AdvisorDoesNotExist", None

        instance.save()
        return instance, new_password

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'advisor'
        ]
