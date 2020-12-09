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
    def create_submission(self, submitter, document):
        id_submission = IDSubmission(
            submitter=submitter,
            document=document
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
