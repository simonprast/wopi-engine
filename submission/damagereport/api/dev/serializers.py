#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import exceptions, serializers

from submission.damagereport.models import DamageReport, Message
from submission.insurancesubmission.models import InsuranceSubmission


class DamageReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    policy_id = serializers.CharField()
    message = serializers.CharField()

    def validate_message(self, message):
        if len(message) > 1500:
            raise serializers.ValidationError(
                'Maximum message length is 1500.')
        return message

    def get_policy(self, submitter, policy_id):
        try:
            policy = InsuranceSubmission.objects.get(
                submitter=submitter, policy_id=policy_id, active=True
            )
            return policy
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def save(self, user):
        policy = self.get_policy(
            submitter=user, policy_id=self.validated_data.get('policy_id'))

        report, message = DamageReport.objects.create_report(
            submitter=user,
            message_body=self.validated_data.get('message'),
            policy=policy
        )

        return report, message


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    message = serializers.CharField()

    def save(self, user, report, internal):
        message = Message(
            report=report,
            sender=user,
            message_body=self.validated_data.get('message'),
            internal=internal
        )
        message.save()
        return message


class GetDamageReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    policy_id = serializers.CharField()
    submitter = serializers.CharField()
