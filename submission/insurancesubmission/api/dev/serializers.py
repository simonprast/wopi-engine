#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import json

from rest_framework import serializers

from insurance.models import Insurance

from submission.insurancesubmission.field_validation import field_validation
from submission.insurancesubmission.models import InsuranceSubmission


def create_data(initial_data):
    # Get the insurance object's fields through the given 'key'
    key = initial_data['key']
    fields = json.loads(Insurance.objects.get(
        insurance_key=key).insurance_fields)

    # Data list containing submission meta data and field data
    data = []
    meta_data = {}
    field_data = []

    if 'provider_id' in initial_data:
        meta_data.update({'provider_id': initial_data['provider_id']})

    data.append(meta_data)

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
            field_data.append(data_field)

    data.append(field_data)

    return data


class InsuranceSubmissionSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)

    def validate(self, data):
        # If any error happens within field_validation, a serializers.ValidationError will be raised
        field_validation(self.initial_data)
        return data

    def save(self, user):
        # Create the data JSON string using the insurance's fields and the
        # content for InsuranceSubmission.data using create_data().
        processed_data = create_data(self.initial_data)

        in_submission = InsuranceSubmission.objects.create_submission(
            insurance_key=self.validated_data.get('key'),
            submitter=user,
            data=processed_data
        )

        return in_submission
