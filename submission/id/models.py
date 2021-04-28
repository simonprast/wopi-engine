#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import os
import uuid

from django.conf import settings
from django.db import models

from user.models import User


class IDSubmissionManager(models.Manager):
    def create_submission(self, submitter, document, document_back):
        id_submission = IDSubmission(
            submitter=submitter,
            document=document,
            document_back=document_back
        )

        id_submission.save()

        return id_submission


def create_path(instance, filename):
    folder = 'ids/' + str(uuid.uuid4())
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder))
    return os.path.join(folder, filename)


class IDSubmission(models.Model):
    submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    # Will be saved to settings.MEDIA_ROOT (francy.media) + /ids/
    document = models.ImageField(
        upload_to=create_path
    )
    document_back = models.ImageField(
        upload_to=create_path, blank=True, null=True
    )
    verified = models.BooleanField(default=False)
    denied = models.BooleanField(default=False)
    latest = models.BooleanField(default=True)

    objects = IDSubmissionManager()

    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        IDSubmission.objects.filter(
            submitter=self.submitter, latest=True).update(latest=False)
        self.latest = True
        super(IDSubmission, self).save()

    class Meta:
        verbose_name = 'ID Submission'

    def __str__(self):
        return 'Ausweis von ' + str(self.submitter) + \
            ' (verified: ' + str(self.verified) + \
            ', latest: ' + str(self.latest) + ')'


class IDToken(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
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
    uploaded = models.BooleanField(
        default=False, null=True, blank=True
    )
    expired = models.BooleanField(
        default=False, null=True, blank=True
    )
