#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


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


class InsuranceSubmission(models.Model):
    insurance = models.ForeignKey(
        Insurance, on_delete=models.SET_NULL, blank=True, null=True
    )
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
