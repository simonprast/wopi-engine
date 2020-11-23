#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import json

from datetime import datetime

from rest_framework import serializers

from submission.models import Submission
from insurance.models import Insurance


class SubmitSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)
    submitter = serializers.CharField(max_length=128)
    data = serializers.CharField(required=False)

    def validate(self, data):
        key = self.initial_data['key']
        self.validate_key(value=key)
        fields = json.loads(Insurance.objects.get(
            insurance_key=key).insurance_fields)

        validated_data = []
        errors = {}

        for field in fields:
            f_key = field['field_name']
            f_title = field['field_title']
            f_type = field['field_type']
            f_required = field['required'] if 'required' in field else False
            f_min = None
            f_max = None
            if 'field_detail' in field:
                f_min = field['field_detail']['min'] if 'min' in field['field_detail'] else None
                if type(f_min) is not int and f_min is not None:
                    raise serializers.ValidationError(
                        {'Internal error': ['Minimum argument at field \'' + f_key + '\' is not an integer.']})

                f_max = field['field_detail']['max'] if 'max' in field['field_detail'] else None
                if type(f_max) is not int and f_max is not None:
                    raise serializers.ValidationError(
                        {'Internal error': ['Maximum argument at field \'' + f_key + '\' is not an integer.']})

            # {
            #     "field_name": "kfz_bm",
            #     "field_title": "BM-Stufe",
            #     "field_type": "integer",
            #     "field_detail": {
            #     "min": 1,
            #     "max": 9
            #     },
            #     "required": true
            # }

            if f_key in self.initial_data:
                content = self.initial_data[f_key]

                if f_type not in ['string', 'text', 'number', 'integer', 'birthdate']:
                    raise serializers.ValidationError(
                        {'Internal error': ['Type \'' + f_type + '\' at field \'' + f_key + '\' is not a valid field '
                                            'type. Valid are string, text, number, integer and birthdate']})

                # Validating the custom types
                # Starting with type 'string'.
                # 'min' and 'max' determine the minimum or maximum length of the string.
                if f_type == 'string':
                    if f_min:
                        if len(content) < f_min:
                            errors.update({f_key: ['String must be at least ' + f_min + 'characters long. Length: '
                                                   + len(content)]})
                    if f_max:
                        if len(content) > f_max:
                            errors.update({f_key: ['String must be at most ' + f_max + 'characters long. Length: '
                                                   + len(content)]})

                # 'integer' must be an integer, who would have thought? ;)
                # 'min' and 'max' determine the minimum or maximum value of the number
                elif f_type == 'integer':
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
                                errors.update({f_key: ['\'' + content + '\' minimum value is ' + f_min + '. Value: '
                                                       + float(content)]})
                        if f_max:
                            if float(content) > f_max:
                                errors.update({f_key: ['\'' + content + '\' maximum value is ' + f_max + '. Value: '
                                                       + float(content)]})

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
                                errors.update({f_key: ['\'' + content + '\' minimum value is ' + f_min + '. Value: '
                                                       + float(content)]})
                        if f_max:
                            if float(content) > f_max:
                                errors.update({f_key: ['\'' + content + '\' maximum value is ' + f_max + '. Value: '
                                                       + float(content)]})

                # 'text' can be any text with a maximum of 1500 characters.
                elif f_type == 'text':
                    if len(content) > 1500:
                        errors.update({f_key: [
                                      'Text must be at most ' + f_max + 'characters long. Length: ' + len(content)]})

                # Birthdate must be a string in the format of DD-MM-YYYY
                elif f_type == 'birthdate':
                    format = '%d-%m-%Y'
                    try:
                        datetime.strptime(content, format)
                    except ValueError:
                        errors.update(
                            {f_key: ['Birthdate must be in format DD-MM-YYYY. Value: ' + content]})

                f_valid = {
                    'field_name': f_key,
                    'field_title': f_title,
                    'field_content': content
                }

                validated_data.append(f_valid)
            else:
                if f_required is not True and f_required is not False:
                    raise serializers.ValidationError(
                        {'Internal error': ['Tag \'required\' neither true nor false.']})
                if f_required is True:
                    errors.update({f_key: ['This field is required.']})

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def validate_key(self, value):
        if not Insurance.objects.filter(insurance_key=value):
            raise serializers.ValidationError(
                'No Insurance found with given key')
        return value

    def create_data(self):
        key = self.initial_data['key']
        fields = json.loads(Insurance.objects.get(
            insurance_key=key).insurance_fields)

        data = []

        for field in fields:
            f_key = field['field_name']
            f_title = field['field_title']

            if f_key in self.initial_data:
                content = self.initial_data[f_key]

                data_field = {
                    'field_name': f_key,
                    'field_title': f_title,
                    'field_content': content
                }

                data.append(data_field)

        return data

    def save(self):
        processed_data = self.create_data()

        submission = Submission.objects.create_submission(
            insurance_key=self.validated_data.get('key'),
            submitter=self.validated_data.get('submitter'),
            data=processed_data
        )

        return submission
