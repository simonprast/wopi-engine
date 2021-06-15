#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#

import os
import uuid

from django.conf import settings
from django.db import models

from insurance.models import Insurance
from user.models import User


class InsuranceSubmissionManager(models.Manager):
    def create_submission(self, insurance_key, submitter, data):
        # Need to get the Insurance object in order to create the Submission object with the relation
        insurance = Insurance.objects.get(insurance_key=insurance_key)

        # self.check_submission returns False in case the exact same submission already exists
        if not self.check_submission(insurance=insurance, submitter=submitter, data=data):
            return 'DuplicateError'

        submission = InsuranceSubmission(
            insurance=insurance,
            submitter=submitter,
            data=data
        )

        submission.save()

        return submission

    def check_submission(self, insurance, submitter, data):
        duplicate = InsuranceSubmission.objects.filter(
            insurance=insurance,
            submitter=submitter,
            data=data
        ).count()

        return False if duplicate > 0 else True


def create_path(instance, filename):
    folder = 'policy/' + str(uuid.uuid4())
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder))
    return os.path.join(folder, filename)


class InsuranceSubmission(models.Model):
    datetime = models.DateTimeField(
        auto_now_add=True
    )
    insurance = models.ForeignKey(
        Insurance, on_delete=models.SET_NULL, blank=True, null=True
    )
    policy_document = models.FileField(
        upload_to=create_path, null=True, blank=True
    )

    # This is the status field, which can either be w(aiting), o(pen), or c(losed).
    status = models.IntegerField(default=0)

    submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    active = models.BooleanField(default=False)
    denied = models.BooleanField(default=False)

    # This field sets a custom policy number/identification code
    policy_id = models.CharField(max_length=64, blank=True, null=True)

    # Data contains the submission data which each field represented through a
    # dictionary with the keys 'field_name', 'field_title' and 'field_content'.
    data = models.TextField()

    objects = InsuranceSubmissionManager()

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Insurance Submission'

    # When showing the name of a submission, return this instead of 'Submission object'
    def __str__(self):
        # Checking for this, as the submission_insurance field can also be None when deleting an insurance
        if self.insurance:
            return 'Anfrage zu ' + str(self.insurance) + ' von ' + str(self.submitter)
        else:
            return 'Anfrage von ' + str(self.submitter)


class Document(models.Model):
    title = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    insurance_submission = models.ForeignKey(
        InsuranceSubmission, on_delete=models.CASCADE, null=True, blank=True
    )
    template = models.FileField(
        upload_to=create_path, null=True, blank=True
    )
    document = models.FileField(
        upload_to=create_path, null=True, blank=True
    )
    signature = models.ImageField(
        upload_to=create_path, default=None, blank=True
    )
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True)
    page_index = models.IntegerField(null=True, blank=True)


class DocumentToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, null=True, blank=True
    )
    token = models.UUIDField(
        default=uuid.uuid4, null=True, blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True
    )
    called = models.BooleanField(
        default=False, null=True, blank=True
    )
    signed = models.BooleanField(
        default=False, null=True, blank=True
    )
    expired = models.BooleanField(
        default=False, null=True, blank=True
    )
