#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#

from django.core.mail import send_mail

from rest_framework import serializers

from user.models import User, VerifyEmailToken

from user.create_or_login import validated_user_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password', 'is_admin']


class UserDetailSerializer(serializers.Serializer):
    first_name, last_name, email, phone, password = None, None, None, None, None
    address_1 = serializers.CharField(required=False)
    address_2 = serializers.CharField(required=False)
    zipcode = serializers.CharField(required=False)

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

        if user:
            user.address_1 = self.validated_data.get('address_1')
            user.address_2 = self.validated_data.get('address_2')
            user.zipcode = self.validated_data.get('zipcode')
            user.save()

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
    address_1 = serializers.CharField(required=False)
    address_2 = serializers.CharField(required=False)
    zipcode = serializers.CharField(required=False)

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
        old_email = instance.email
        instance.email = self.email or instance.email
        instance.phone = self.phone or instance.phone
        instance.address_1 = validated_data.get(
            'address_1') or instance.address_1
        instance.address_2 = validated_data.get(
            'address_2') or instance.address_2
        instance.zipcode = validated_data.get('zipcode') or instance.zipcode

        new_password = False
        if self.password and not instance.check_password(self.password):
            instance.set_password(self.password)
            new_password = True

        if self.initial_data.get('advisor'):
            try:
                advisor = User.objects.get(
                    pk=self.initial_data.get('advisor'), utype=7)
                instance.advisor = advisor
            except User.DoesNotExist:
                return "AdvisorDoesNotExist", None

        if self.email and old_email != self.email:
            instance.verified = False
            VerifyEmailToken.objects.filter(user=instance).delete()
            verify_email_token = VerifyEmailToken(user=instance)
            verify_email_token.save()

            mail_message = \
                'Hallo ' + instance.first_name + '!' \
                '<br><br>Deine E-Mail Adresse wurde geändert.' \
                '<br><br>Um deine E-Mail Adresse zu bestätigen, klick bitte auf folgenden Link:' \
                '<br><a href="https://app.spardaplus.at/?v=' + str(verify_email_token.token) + \
                '">https://app.spardaplus.at/?v=' + \
                str(verify_email_token.token) + '</a>'

            send_mail(
                'Bestätigung Deiner neuen E-Mail Adresse',
                mail_message,
                None,
                [self.email],
                fail_silently=False,
                html_message=mail_message
            )

        instance.save()
        return instance, new_password

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'advisor',
            'address_1',
            'address_2',
            'zipcode'
        ]
