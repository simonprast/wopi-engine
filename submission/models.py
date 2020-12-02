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


class SubmissionManager(models.Manager):
    def create_submission(self, insurance_key, submitter, data):
        # Need to get the Insurance object in order to create the Submission object with the relation
        insurance = Insurance.objects.get(insurance_key=insurance_key)

        # self.check_submission returns False in case the exact same submission already exists
        if not self.check_submission(insurance=insurance, submitter=submitter, data=data):
            return 'DuplicateError'

        submission = Submission(
            submission_insurance=insurance,
            submission_submitter=submitter,
            submission_data=data
        )

        submission.save()

        return submission

    def check_submission(self, insurance, submitter, data):
        duplicate = Submission.objects.filter(
            submission_insurance=insurance,
            submission_submitter=submitter,
            submission_data=data
        ).count()

        return False if duplicate > 0 else True


class Submission(models.Model):
    submission_insurance = models.ForeignKey(
        Insurance, on_delete=models.SET_NULL, blank=True, null=True
    )
    submission_submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    submission_data = models.TextField()

    objects = SubmissionManager()

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Insurance Submission'

    # When showing the name of a submission, return this instead of 'Submission object'
    def __str__(self):
        # Checking for this, as the submission_insurance field can also be None when deleting an insurance
        if self.submission_insurance:
            return 'Anfrage zu ' + str(self.submission_insurance) + ' von ' + str(self.submission_submitter)
        else:
            return 'Anfrage von ' + str(self.submission_submitter)


class IDSubmissionManager(models.Manager):
    def create_idsubmission(self, submission_submitter, id_document):
        id_submission = IDSubmission(
            submission_submitter=submission_submitter,
            submission_id=id_document
        )

        id_submission.save()

        return id_submission


def create_path(instance, filename):
    folder = 'ids/' + str(uuid.uuid4())
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder))
    return os.path.join(folder, filename)


class IDSubmission(models.Model):
    submission_submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    # Will be saved to settings.MEDIA_ROOT (francy.media) + /ids/
    submission_id = models.ImageField(
        upload_to=create_path
    )
    verified = models.BooleanField(default=False)
    latest = models.BooleanField(default=True)

    objects = IDSubmissionManager()

    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        IDSubmission.objects.filter(
            submission_submitter=self.submission_submitter, latest=True).update(latest=False)
        self.latest = True
        super(IDSubmission, self).save()

    class Meta:
        verbose_name = 'ID Submission'

    def __str__(self):
        return 'Ausweis von ' + str(self.submission_submitter) + \
            ' (verified: ' + str(self.verified) + \
            ', latest: ' + str(self.latest) + ')'
