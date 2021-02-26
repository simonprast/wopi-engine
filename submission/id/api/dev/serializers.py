#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import serializers

from submission.id.models import IDSubmission


class IDSubmissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    submitter = serializers.CharField(required=False)
    document = serializers.ImageField()
    document_back = serializers.ImageField(required=False)
    verified = serializers.BooleanField(required=False)
    latest = serializers.BooleanField(required=False)
    denied = serializers.BooleanField(required=False)

    def save(self, user):
        submission = IDSubmission.objects.create_submission(
            submitter=user,
            document=self.validated_data.get('document'),
            document_back=self.validated_data.get('document_back')
        )

        return submission.document.url
