#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#

from datetime import datetime, timezone

from django.db.models import Q

from mail_templated import EmailMessage

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response

from submission.damagereport.models import DamageReport, Image, Message
from submission.insurancesubmission.models import InsuranceSubmission

from .serializers import DamageReportSerializer, GetDamageReportSerializer, MessageSerializer


class SubmitDamageReport(generics.GenericAPIView):
    queryset = DamageReport.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_objects(self, user, latest=True):
        try:
            submission = DamageReport.objects.filter(
                submitter=user, denied=False)
            return submission
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get_policy(self, policy_id, user):
        try:
            policy = InsuranceSubmission.objects.get(
                submitter=user, policy_id=policy_id)
            return policy
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def check_active_report(self, user, policy):
        active_open_reports = DamageReport.objects.filter(
            submitter=user,
            policy=policy,
            status='o'
        )
        active_waiting_reports = DamageReport.objects.filter(
            submitter=user,
            policy=policy,
            status='w'
        )

        if active_open_reports.count() > 0:
            open_report = DamageReport.objects.get(submitter=user,
                                                   policy=policy,
                                                   status='o'
                                                   )
            if open_report.denied:
                return True, None
            return False, open_report
        if active_waiting_reports.count() > 0:
            open_report = DamageReport.objects.get(submitter=user,
                                                   policy=policy,
                                                   status='w'
                                                   )
            if open_report.denied:
                return True, None
            return False, open_report

        return True, None

    # POST new damage report (user)
    def post(self, request, *args, **kwargs):
        if not request.data.__contains__('policy_id'):
            return Response({'policy_id': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        policy_id = request.data.get('policy_id')
        policy = self.get_policy(policy_id, request.user)
        check_report, open_report = self.check_active_report(
            user=request.user, policy=policy)

        if not check_report:
            return Response(
                {'open_report': ['There is already an open report for this policy'],
                 'id': open_report.id}, status=status.HTTP_400_BAD_REQUEST)
        # images = request.data.__getitem__('email'),
        # request.data.__getitem__('password')
        serializer = DamageReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report, message = serializer.save(user=request.user)

        print(request.data)

        if request.data.__contains__('images'):
            for image in request.data.getlist('images'):
                img = Image(image=image, message=message)
                img.save()

        print(request.data.get('images'))

        return Response(serializer.data)


class OpenCloseDamageReport(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    # POST - change a damage report's status from o/w to c or back to w (admin)
    def post(self, request, report, *args, **kwargs):
        report = self.get_report(pk=report)

        if not report.submitter == request.user and not request.user.is_staff:
            raise exceptions.PermissionDenied

        if report.status != 'c':
            report.status = 'o'

            message = Message(
                report=report,
                message_body='DAMAGEREPORTCLOSEDNOWMESSAGE',
                sender=request.user
            )

            message.save()

        if report.status == 'c':
            report.status = 'w'

            message = Message(
                report=report,
                message_body='DAMAGEREPORTOPENEDNOWMESSAGE',
                sender=request.user
            )

            message.save()

        return Response({'status': report.status}, status=status.HTTP_200_OK)


class SendMessage(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_report(self, pk):
        try:
            report = DamageReport.objects.get(pk=pk)
            return report
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get_latest_message(self, report, user):
        try:
            message = list(Message.objects.filter(
                report=report, sender=user))[-1]
            print(message)
            return message
        except Message.DoesNotExist:
            raise exceptions.NotFound

    def get_images(self, message):
        images = Image.objects.filter(message=message)
        return images

    def post(self, request, report, *args, **kwargs):
        report = self.get_report(pk=report)

        if not report.submitter == request.user and not request.user.is_staff:
            raise exceptions.PermissionDenied

        if report.status == 'c':
            return Response(
                {'status_closed': [
                    'This report\'s status is closed. You cannot submit any more messages to this report.']},
                status=status.HTTP_403_FORBIDDEN)

        sender = request.user

        if Message.objects.filter(report=report, sender=sender).count() > 0:
            difference = (
                datetime.now(timezone.utc) -
                self.get_latest_message(report, sender).datetime
            ).total_seconds()
            if difference < 20:
                return Response(
                    {
                        'antispam': ['Time difference since the last message received is too low.'],
                        'time_remaining': 20-difference
                    },
                    status=status.HTTP_403_FORBIDDEN)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(user=sender, report=report)

        if request.data.__contains__('images'):
            for image in request.data.getlist('images'):
                img = Image(image=image, message=message)
                img.save()

        if sender.is_staff:
            mail_context = {
                'user': report.submitter
            }

            mail_message = EmailMessage(
                'mailing/new-message-german.tpl',
                mail_context,
                None,
                [report.submitter.email]
            )

            mail_message.send()

        message_dict = {
            'message': message.message_body
        }

        images = self.get_images(message=message)

        if images.count() > 0:
            message_images = []
            for image in images:
                message_images.append({
                    'url': image.image.url
                })
            message_dict.update({
                'images': message_images
            })

        return Response(message_dict, status=status.HTTP_200_OK)


class GetDamageReports(generics.GenericAPIView):
    queryset = DamageReport.objects.all()
    serializer_class = GetDamageReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_user_reports(self, user):
        try:
            reports = DamageReport.objects.filter(
                submitter=user, denied=False)
            return reports
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get_admin_reports(self, user):
        try:
            users = user.user_set.all()

            reports = []
            for user in users:
                query_reports = DamageReport.objects.filter(
                    Q(status='w') | Q(status='o'), submitter=user)
                if query_reports:
                    reports.extend(list(query_reports))
            return reports
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get(self, request, *args, **kwargs):
        # A staff user is allowed to see all drs
        if request.user.is_staff:
            reports = self.get_admin_reports(user=request.user)
        # AnonymousUsers are denied.
        # If the User is not anonymous, only show drs of the requesting users.
        else:
            reports = self.get_user_reports(user=request.user)

        report_list = create_report_list(reports)
        return Response(report_list, status=status.HTTP_200_OK)


class GetAllDamageReports(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get_reports(self):
        try:
            reports = DamageReport.objects.filter(
                Q(status='w') | Q(status='o'))
            return reports
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get(self, request, *args, **kwargs):
        reports = self.get_reports()
        report_list = create_report_list(reports)
        return Response(report_list, status=status.HTTP_200_OK)


class GetDamageReportDetails(generics.GenericAPIView):
    queryset = DamageReport.objects.all()
    serializer_class = DamageReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_report(self, pk):
        try:
            submission = DamageReport.objects.get(pk=pk)
            return submission
        except DamageReport.DoesNotExist:
            raise exceptions.NotFound

    def get_messages(self, report):
        try:
            messages = Message.objects.filter(report=report)
            return messages
        except Message.DoesNotExist:
            raise exceptions.NotFound

    def get_images(self, message):
        images = Image.objects.filter(message=message)
        return images

    def get(self, request, pk, *args, **kwargs):
        report = self.get_report(pk=pk)

        if not report.submitter == request.user and not request.user.is_staff:
            raise exceptions.PermissionDenied

        report_log = {}

        report_creator = report.submitter
        report_date = str(report.datetime)
        report_policy_name = str(
            report.policy.insurance) if report.policy else None
        report_policy_id = report.policy.policy_id if report.policy else None

        report_log.update({
            'id': report.id,
            'creator': str(report_creator),
            'date': report_date,
            'policy_name': report_policy_name,
            'policy_id': report_policy_id,
            'status': report.status
        })

        messages = self.get_messages(report=report)

        message_list = []

        for message in messages:
            date = str(message.datetime)
            sender = message.sender
            body = message.message_body
            picture = sender.picture.url if sender.picture else None

            message_dict = {
                'date': date,
                'sender': {
                    'creator': sender == report_creator,
                    'name': str(sender),
                    'picture': picture
                },
                'body': body
            }

            images = self.get_images(message=message)

            if images.count() > 0:
                message_images = []
                for image in images:
                    message_images.append({
                        'url': image.image.url
                    })
                message_dict.update({
                    'images': message_images
                })

            message_list.append(message_dict)

        report_log.update({
            'messages': message_list
        })

        return Response(report_log)


def create_report_list(self, reports):
    report_list = []
    for report in reports:
        report_obj = {
            'id': report.id,
            'policy': {
                'id': report.policy.id if report.policy else None,
                'name': str(report.policy.insurance) if report.policy else None,
                'policy_id': report.policy.policy_id if report.policy else None
            },
            'submitter': str(report.submitter),
            'status': report.status
        }

        report_list.append(report_obj)

    return report_list
