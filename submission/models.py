#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


# from django.conf import settings
from django.db import models

from insurance.models import Insurance


class SubmissionManager(models.Manager):
    def create_submission(self, insurance_key, submitter, data):
        insurance = Insurance.objects.get(insurance_key=insurance_key)

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
        Insurance, on_delete=models.SET_NULL, blank=True, null=True)
    submission_submitter = models.CharField(max_length=128, blank=True)
    submission_data = models.TextField()

    objects = SubmissionManager()

    REQUIRED_FIELDS = []

    def __str__(self):
        if self.submission_insurance:
            return 'Anfrage zu ' + self.submission_insurance.insurance_name + ' von ' + self.submission_submitter
        else:
            return 'Anfrage von ' + self.submission_submitter

    # def save(self, *args, **kwargs):
    #     super(User, self).save(*args, **kwargs)
