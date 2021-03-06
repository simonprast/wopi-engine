#
# Created on Wed Nov 25 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.conf import settings

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from rest_framework import serializers, status

from .authentication import obtain_auth_token
from .models import User, check_phone_number


def create_or_login(regSerializer, logSerializer, request, validated=False):
    register_serializer = regSerializer
    login_serializer = logSerializer
    user_created = False

    if settings.ALLOW_REGISTER:
        if not validated:
            if not register_serializer.is_valid() and not login_serializer.is_valid():
                raise serializers.ValidationError(
                    register_serializer.errors)

        if register_serializer.is_valid():
            # Creates the user using User.objects.create_user()
            # This returns True in case the User object is succesfully created
            user_created = register_serializer.save()
        elif User.objects.filter(email=request.data.__getitem__('email')).count() == 0:
            raise serializers.ValidationError(
                register_serializer.errors)

    # Authenticate the newly created user
    # OR authenticate the existing user with given username and password combination.
    token, created, user = obtain_auth_token(
        # This argument takes a username, but the UserDetailSerializer sets the given email as the user's username
        request.data.__getitem__('email'),
        request.data.__getitem__('password')
    )

    # If a user with given username does already exist but the username-password
    # combination is wrong, 'token', 'created' and 'user' will be set to 'None'.
    # In this case, this error response is thrown.
    if not token:
        errors = {
            'LoginDenied': [
                'user with this email already exists',
                'email and password combination wrong'
            ]
        }
        raise serializers.ValidationError(errors)
        # return Response(errors, status=status.HTTP_403_FORBIDDEN), None, None

    # Either the user object was created or the user just logged in
    auth_status = status.HTTP_201_CREATED if user_created or created else status.HTTP_200_OK

    # Attach a 'created' confirmation to the return dictionary if one of the objects was just created
    return_dict = {
        'email': user.email,
        'token': token.key,
        'token_created': created,
        'user_created': user_created
    }

    return return_dict, auth_status, user


def validated_user_data(initial_data, change=False):
    first_name, last_name, email, phone, password = None, None, None, None, None

    # Dict of field errors
    errors = {}

    # fields = [
    #     {
    #         'field_name': 'first_name',
    #         'field_title': 'Vorname',
    #         'field_type': 'string'
    #     },
    #     {
    #         'field_name': 'last_name',
    #         'field_title': 'Nachname',
    #         'field_type': 'string'
    #     },
    #     {
    #         'field_name': 'email',
    #         'field_title': 'E-Mail Adresse',
    #         'field_type': 'email',
    #     },
    #     {
    #         'field_name': 'phone',
    #         'field_title': 'Telefonnummer',
    #         'field_type': 'phone',
    #     },
    # ]

    # initial_data contains the POST request's data
    # Check if the field's key is in the POST body
    names = ['first_name', 'last_name']
    for name in names:
        if name in initial_data:
            content = initial_data[name]

            if content == '':
                errors.update(
                    {name: ['This field may not be blank.']})
            elif len(content) > User._meta.get_field('first_name').max_length:
                errors.update(
                    {name: ['Text must be at most ' + str(User._meta.get_field('first_name').max_length) +
                            ' characters long. Length: ' + str(len(content))]})
            else:
                if name == 'first_name':
                    first_name = content
                elif name == 'last_name':
                    last_name = content
        else:
            # 'change' is set to true if the user object is altered.
            # In this case, the fields aren't required.
            if not change:
                errors.update(
                    {name: ['This field is required.']})

    if 'email' in initial_data:
        email_to_validate = initial_data['email']
        try:
            validate_email(email_to_validate)
            email = email_to_validate
        except ValidationError:
            errors.update(
                {'email': ['This seems to be not a valid email.']})
    else:
        if not change:
            errors.update(
                {'email': ['This field is required.']})

    if 'phone' in initial_data:
        phone_number = check_phone_number(initial_data['phone'])
        if not phone_number:
            errors.update(
                {'phone': ['Invalid number.']})
        else:
            phone = phone_number

    if 'password' in initial_data:
        password_to_validate = initial_data['password']
        try:
            validate_password(password_to_validate)
            password = password_to_validate
        except ValidationError:
            errors.update(
                {'password': ['Given password does not match the requirements.'
                              ' (Min-length 8, alphanumeric, not common and not similar to user data)']})
        if change and 'current_password' in initial_data:
            if password == initial_data['current_password']:
                errors.update(
                    {'password_match': ['The new password matches the current password.']})
    else:
        if not change:
            errors.update(
                {'password': ['This field is required.']})

    # If any errors are in the error dictionary, raise those errors
    if errors:
        raise serializers.ValidationError(errors)

    return first_name, last_name, email, phone, password
