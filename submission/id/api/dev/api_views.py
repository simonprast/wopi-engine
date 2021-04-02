#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#

from datetime import datetime, timezone

from mail_templated import EmailMessage

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from submission.id.models import IDSubmission, IDToken

from user.models import User

from user.api.dev.serializers import ChangeUserSerializer

from .serializers import IDSubmissionSerializer


class HandleDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = IDSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user, latest=True):
        try:
            submission = IDSubmission.objects.get(
                submitter=user, latest=latest)
            return submission
        except IDSubmission.DoesNotExist:
            raise exceptions.NotFound

    # GET - shown own, latest ID document and verified status (customer)
    # GET - show all latest, unverified ID documents (admin)
    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            submissions = IDSubmission.objects.filter(
                verified=False, latest=True, denied=False)
            serializer = IDSubmissionSerializer(submissions, many=True)
            return Response(serializer.data)
        else:
            submission = self.get_object(user=request.user)
            serializer = IDSubmissionSerializer(submission)
            return Response(serializer.data)

    # POST - submit ID document (customer)
    def post(self, request, *args, **kwargs):
        serializer = IDSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_document = serializer.save(user=request.user)
        return Response({'submission_id': str(id_document)})


class VerifyDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    # Using the user.api.<v>.ChangeUserSerializer, as the context attribute
    # is included when calling the serializer using self.get_serializer().
    # The context attribute is needed for identifying the request method.
    # (Alter user data on ID verification)
    serializer_class = ChangeUserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, pk):
        try:
            submission = IDSubmission.objects.get(pk=pk)
            return submission
        except IDSubmission.DoesNotExist:
            raise exceptions.NotFound

    # PUT - set verified field value of a specific ID object (admin)
    def put(self, request, pk, *args, **kwargs):
        submission = self.get_object(pk=pk)
        user = submission.submitter

        if request.data.__contains__('verified') or request.data.__contains__('denied'):
            if request.data.__contains__('denied'):
                if type(request.data.get('denied')) == bool:
                    # Set the denied status of the id
                    denied = request.data.get('denied')

                    # Todo: Mail Sending

                    submission.denied = denied
                else:
                    return Response({'denied': ['Value must be a bool.']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                denied = submission.denied

            if request.data.__contains__('verified'):
                if type(request.data.get('verified')) == bool:
                    # Set the varified status of the id
                    verified = request.data.get('verified')

                    if submission.verified is False and verified is True:
                        mail_context = {
                            'user': user
                        }

                        mail_message = EmailMessage(
                            'mailing/verify-id-german.tpl',
                            mail_context,
                            None,
                            [user.email]
                        )

                        mail_message.send()

                    submission.verified = verified
                else:
                    return Response({'verified': ['Value must be a bool.']}, status=status.HTTP_400_BAD_REQUEST)
            else:
                verified = submission.verified

            submission.save()

            # Update the user object using the ChangeUserSerializer.
            partial = kwargs.pop('partial', False)
            instance = user
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            user, new_password = serializer.update(
                instance, serializer.validated_data)

            if user == "AdvisorDoesNotExist":
                return Response({'advisor_does_not_exist': 'No advisor with given UUID found.'},
                                status=status.HTTP_400_BAD_REQUEST)

            return Response({'success': True, 'verified': verified, 'denied': denied, 'submission': str(submission),
                             'user': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'verified or denied': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'submission_id': 'ok'})


class UserDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = IDSubmissionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_user(self, pk):
        try:
            user = User.objects.get(pk=pk)
            return user
        except User.DoesNotExist:
            raise exceptions.NotFound

    # GET - all IDs of a single user (admin)
    def get(self, request, pk, *args, **kwargs):
        user = self.get_user(pk=pk)
        submissions = IDSubmission.objects.filter(submitter=user)
        serializer = IDSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class IDTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        time_left = 60
        if IDToken.objects.filter(user=request.user).exists():
            token = IDToken.objects.get(user=request.user)
        else:
            token = IDToken.objects.create(user=request.user)

        time_since = (datetime.now(timezone.utc) - token.created_at).total_seconds()
        if time_since < 60:
            time_left = 60-time_since
        else:
            token.delete()
            token = IDToken.objects.create(user=request.user)

        return Response({'token': str(token.token), 'time_left': time_left})

    def post(self, request, *args, **kwargs):
        if IDToken.objects.filter(token=request.data['token']).exists():
            token = IDToken.objects.get(token=request.data['token'])
            if (datetime.now(timezone.utc) - token.created_at).total_seconds() < 60:
                token.called = True
                token.save()
                return Response(
                    {'success': 'The Token has been called.'},
                    status=status.HTTP_200_OK
                )
            else:
                token.delete()
        return Response(
                {'TokenNotFound': 'Given token was not found.'},
                status=status.HTTP_403_FORBIDDEN
            )
