#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.db import models


class InsuranceManager(models.Manager):
    # This can be used in the future to dynamically create new insurances through the API
    pass


class Insurance(models.Model):
    insurance_name = models.CharField(max_length=40, unique=True)
    insurance_key = models.CharField(max_length=30, unique=True)
    insurance_subtitle = models.CharField(max_length=70)

    # Insurances will be defined at the insurance field
    insurance_fields = models.TextField()
    # Follow following JSON format to have a valid insurance model:
    # [
    #   {
    #     "field_name": "kfz_bm",
    #     "field_title": "BM-Stufe",
    #     "field_type": "integer",
    #     "field_detail": {
    #       "min": 1,
    #       "max": 9
    #     },
    #     "required": true
    #   }
    # ]
    #
    # 'required', 'field_detail' and its arguments ('min', 'max') are optional

    objects = InsuranceManager()

    REQUIRED_FIELDS = []

    # When showing the short name of an insurance, return the insurance name instead of 'Insurance object'
    def __str__(self):
        return self.insurance_name
