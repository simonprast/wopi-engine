from rest_framework import serializers

from submission.insurancesubmission.field_validation import field_validation


class InsuranceCalculateSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=30)

    def validate(self, data):
        # If any error happens within field_validation, a serializers.ValidationError will be raised
        custom_data_dict = field_validation(self.initial_data)
        return custom_data_dict
