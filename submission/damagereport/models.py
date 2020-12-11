#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import os
import uuid

from django.conf import settings
from django.db import models

from submission.insurancesubmission.models import InsuranceSubmission
from user.models import User


class DamageReportManager(models.Manager):
    def create_report(self, submitter, message_body, policy=None, policy_id=None):
        if not policy:
            # Need to get the Insurance object in order to create the Submission object with the relation
            try:
                policy = InsuranceSubmission.objects.get(
                    policy_id=policy_id, active=True)
            except InsuranceSubmission.DoesNotExist:
                raise ValueError('No active Policy found with given policy id')

        report = DamageReport(
            policy=policy,
            submitter=submitter
        )

        report.save()

        message = Message(
            report=report,
            sender=submitter,
            message_body=message_body
        )

        message.save()

        return report, message


class DamageReport(models.Model):
    datetime = models.DateTimeField(
        auto_now_add=True
    )
    policy = models.ForeignKey(
        InsuranceSubmission, on_delete=models.SET_NULL, blank=True, null=True
    )
    submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    denied = models.BooleanField(default=False)

    # This is the status field, which can either be w(aiting), o(pen), or c(losed).
    status = models.CharField(max_length=1, default='w')

    objects = DamageReportManager()

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Damage Report'

    # When showing the name of a damage report, return this instead of 'DamageReport object'
    def __str__(self):
        # Checking for this, as the policy field can also be None when deleting an insurance
        if self.policy:
            return 'Schadensmeldung zu ' + str(self.policy.insurance) + ' von ' + str(self.submitter)
        else:
            return 'Schadensmeldung von ' + str(self.submitter)

    def save(self, *args, **kwargs):
        if self.denied is True:
            self.status = 'c'
        super(DamageReport, self).save()


class Message(models.Model):
    datetime = models.DateTimeField(
        auto_now_add=True
    )
    report = models.ForeignKey(
        DamageReport, on_delete=models.CASCADE, blank=True, null=True
    )
    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    message_body = models.TextField(
        max_length=2500
    )

    def save(self, *args, **kwargs):
        if self.report.submitter == self.sender:
            self.report.status = "w"
            self.report.save()
        else:
            self.report.status = "o"
            self.report.save()
        super(Message, self).save()


def create_path(instance, filename):
    folder = 'ids/' + str(uuid.uuid4())
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder))
    return os.path.join(folder, filename)


class Image(models.Model):
    image = models.ImageField(upload_to=create_path)
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, blank=True, null=True
    )
