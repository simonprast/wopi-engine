#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import json

from datetime import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from rest_framework import serializers

from insurance.models import Insurance
from submission.models import Submission
from user.models import User, check_phone_number


def user_validation(initial_data):
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
                {'password': ['Given password does not match the requirements. '
                              '(Min-length 8, alphanumeric, not common and not similar to user data)']})
    else:
        errors.update(
            {'password': ['This field is required.']})

    # If any errors are in the error dictionary, raise those errors
    if errors:
        raise serializers.ValidationError(errors)

    return first_name, last_name, email, phone, password


def field_validation(initial_data):
    # Get the insurance object's fields through the given 'key'
    key = initial_data['key']
    validate_key(value=key)
    # Insurance.insurance_fields is a json string defining insurance fields
    # See insurance.demo.json for details
    fields = json.loads(Insurance.objects.get(
        insurance_key=key).insurance_fields)

    # List of valid submission data dicts
    validated_data = []
    # Dict of field errors
    errors = {}

    for field in fields:
        # Get the properties of the current insurance field
        f_key = field['field_name']
        f_title = field['field_title']
        f_type = field['field_type']

        # Set required to False if it's not specificly defined in the insurance's field
        f_required = field['required'] if 'required' in field else False
        if f_required is not True and f_required is not False:
            # Raise a ValidationError when 'required' is neither True nor False
            raise serializers.ValidationError(
                {'Internal error': ['Tag \'required\' neither true nor false.']})

        # 'f_min' and 'f_max' is only set if those properties are defined within the insurance's field_detail field
        f_min = None
        f_max = None
        if 'field_detail' in field:
            f_min = field['field_detail']['min'] if 'min' in field['field_detail'] else None
            # If 'f_min' (or 'f_max') is not an integer or NoneType, an error occured defining this property
            if type(f_min) is not int and f_min is not None:
                raise serializers.ValidationError(
                    {'Internal error': ['Minimum argument at field \'' + f_key + '\' is not an integer.']})

            f_max = field['field_detail']['max'] if 'max' in field['field_detail'] else None
            if type(f_max) is not int and f_max is not None:
                raise serializers.ValidationError(
                    {'Internal error': ['Maximum argument at field \'' + f_key + '\' is not an integer.']})

        # initial_data contains the POST request's data
        # Check if the field's key is in the POST body
        if f_key in initial_data:
            # content = key's value
            # .. f_key -> content
            content = initial_data[f_key]

            # If the field's type is none of those, an error occured defining this property
            if f_type not in ['string', 'text', 'number', 'integer', 'birthdate']:
                raise serializers.ValidationError(
                    {'Internal error': ['Type \'' + f_type + '\' at field \'' + f_key + '\' is not a valid field '
                                        'type. Valid are string, text, number, integer and birthdate']})

            # Validating the custom types
            # Starting with type 'string'
            # 'min' and 'max' determine the minimum or maximum length of the string
            if f_type == 'string':
                if f_min:
                    if len(content) < f_min:
                        errors.update({f_key: ['String must be at least ' + str(f_min) + ' characters long. Length: '
                                               + str(len(content))]})
                if f_max:
                    if len(content) > f_max:
                        errors.update({f_key: ['String must be at most ' + str(f_max) + ' characters long. Length: '
                                               + str(len(content))]})

            # 'integer' must be an integer, who would have thought? ;)
            # 'min' and 'max' determine the minimum or maximum value of the number
            elif f_type == 'integer':
                # Try to convert 'content' to float. If this is not possible, it is not a valid number.
                # try/except is slow, though (Know a better solution?)
                try:
                    float(content)
                except ValueError:
                    errors.update(
                        {f_key: ['\'' + content + '\' seems to be not a number.']})
                else:
                    if not float(content).is_integer():
                        errors.update(
                            {f_key: ['\'' + content + '\' seems to be not an integer.']})

                    if f_min:
                        if float(content) < f_min:
                            errors.update(
                                {f_key: ['Minimum value is ' + str(f_min) + '. Value: ' + str(content)]})
                    if f_max:
                        if float(content) > f_max:
                            errors.update(
                                {f_key: ['Maximum value is ' + str(f_max) + '. Value: ' + str(content)]})

            # 'number' can be any number (float)
            # 'min' and 'max' determine the minimum or maximum value of the number
            elif f_type == 'number':
                try:
                    float(content)
                except ValueError:
                    errors.update(
                        {f_key: ['\'' + content + '\' seems to be not a number.']})
                else:
                    if f_min:
                        if float(content) < f_min:
                            errors.update(
                                {f_key: ['Minimum value is ' + str(f_min) + '. Value: ' + str(content)]})
                    if f_max:
                        if float(content) > f_max:
                            errors.update(
                                {f_key: ['Maximum value is ' + str(f_max) + '. Value: ' + str(content)]})

            # 'text' can be any text with a maximum of 1500 characters
            elif f_type == 'text':
                if len(content) > 1500:
                    errors.update(
                        {f_key: ['Text must be at most 1500 characters long. Length: ' + str(len(content))]})

            # Birthdate must be a string in the format of DD-MM-YYYY
            elif f_type == 'birthdate':
                # Try to convert 'content' to a datetime object
                # If this is not possible, it is not a valid birthdate
                # try/except is slow, though (Know a better solution?)
                format = '%d-%m-%Y'
                try:
                    datetime.strptime(content, format)
                except ValueError:
                    errors.update(
                        {f_key: ['Birthdate must be in format DD-MM-YYYY. Value: ' + content]})

            # Create a basic dictionary using the content validated above
            f_valid = {
                'field_name': f_key,
                'field_title': f_title,
                'field_content': content
            }

            # Append the dictionary to the list of valid content dictionaries
            validated_data.append(f_valid)
        else:
            if f_required is True:
                errors.update({f_key: ['This field is required.']})

    # If any errors are in the error dictionary, raise those errors
    if errors:
        raise serializers.ValidationError(errors)

    return True


def validate_key(value):
    if not Insurance.objects.filter(insurance_key=value):
        raise serializers.ValidationError(
            'No Insurance found with given key')
    return value


def create_data(initial_data):
    # Get the insurance object's fields through the given 'key'
    key = initial_data['key']
    fields = json.loads(Insurance.objects.get(
        insurance_key=key).insurance_fields)

    # List of dictionaries
    data = []

    for field in fields:
        f_key = field['field_name']
        f_title = field['field_title']

        if f_key in initial_data:
            content = initial_data[f_key]

            # Create a basic dictionary using 'content'. As, at this point, all values
            # were already validated, the content can be assigend to 'field_content'
            data_field = {
                'field_name': f_key,
                'field_title': f_title,
                'field_content': content
            }

            # Append the dictionary to the list of content dictionaries
            data.append(data_field)

    return data


class SubmitSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)

    def validate(self, data):
        # If any error happens within field_validation, a ValidationError will be raised
        field_validation(self.initial_data)
        return data

    def save(self, user):
        # Create the data JSON string using the insurance's fields and the
        # content for Submission.submission_data using create_data().
        processed_data = create_data(self.initial_data)

        submission = Submission.objects.create_submission(
            insurance_key=self.validated_data.get('key'),
            submitter=user,
            data=processed_data
        )

        return submission


class RegisterSubmitSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)

    first_name, last_name, email, phone, password = None, None, None, None, None

    def validate(self, data):
        # If any error happens within field_validation, a ValidationError will be raised
        field_validation(self.initial_data)
        # Through this, it is ensured that all insurance-related fields are valid
        # Further, ensure that the user-related fields are valid
        self.first_name, self.last_name, self.email, self.phone, self.password = user_validation(
            self.initial_data)
        return data

    def save(self):
        # First, create a user object using the submission data
        submitter = User.objects.create_user(
            username=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            password=self.password,
            serializers=serializers
        )

        if not submitter:
            raise serializers.ValidationError(
                {'DuplicateEmail': ['User with this E-Mail already exists.']})

        # Todo: Use user authentication similar to user.api.dev (create_user)
        # Error handling

        # Create the data JSON string using the insurance's fields and the
        # content for Submission.submission_data using create_data().
        processed_data = create_data(self.initial_data)

        submission = Submission.objects.create_submission(
            insurance_key=self.validated_data.get('key'),
            submitter=submitter,
            data=processed_data
        )

        return submission
