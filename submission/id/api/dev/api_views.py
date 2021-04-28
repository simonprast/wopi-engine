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
from .permissions import HasTokenOrIsAuthenticated


class HandleDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = IDSubmissionSerializer
    permission_classes = [HasTokenOrIsAuthenticated]

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
        if request.user.is_anonymous:
            return exceptions.NotAuthenticated

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

        if request.user.is_anonymous:
            if IDToken.objects.filter(token=request.data.get('token')).exists():
                token = IDToken.objects.get(token=request.data.get('token'))

                if token.uploaded:
                    return Response(
                        {'TokenAlreadyUsed': 'The given token has already been used for uploading a document.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    token.uploaded = True
                    token.save()
                id_document = serializer.save(user=token.user)
            else:
                return Response(
                    {'TokenNotFound': 'The given token was not found or is not valid anymore.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if IDToken.objects.filter(user=request.user).exists():
                IDToken.objects.filter(user=request.user).delete()

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

    def post(self, request, *args, **kwargs):
        pass


def refresh_token_validity(user=None, token=None):
    if token and IDToken.objects.filter(token=token).exists():
        token = IDToken.objects.get(token=token)

        expired = False
        time_left = None

        if token.called:
            return token, time_left, expired, token.called, token.uploaded

        time_alive = (datetime.now(timezone.utc) - token.created_at).total_seconds()

        # If the active token is alive for less than 60 seconds, use it.
        if time_alive < 60:
            time_left = 60 - time_alive

        # If the active token is alive for more than 60 and less than
        # 70 seconds, it is considered the currently expired token.
        elif time_alive < 70:
            time_left = 70 - time_alive
            expired = True

        # If the token is alive for more than 70 seconds, it can be deleted.
        else:
            token.delete()
            token = None

        return token, time_left, expired, token.called, token.uploaded

    if user:
        # Initalize variable in case no expired token will be assigned.
        expired_token = None

        if IDToken.objects.filter(user=user).exists():
            tokens = IDToken.objects.filter(user=user)

            # If there exists more than one token for a user, one of them must be expired.
            if tokens.count() > 1:
                expired_token = tokens.get(expired=True)
                ex_time_alive = (datetime.now(timezone.utc) - expired_token.created_at).total_seconds()

                # Delete the expired token in case it has been alive for more than 70 seconds.
                if ex_time_alive >= 70:
                    expired_token.delete()
                    expired_token = None

            # Get the currently active token, ...
            token = tokens.get(expired=False)
        else:
            # ... or create a new one.
            token = IDToken.objects.create(user=user)

        e_called = expired_token.called if expired_token else False

        if token.called or e_called:
            if token.called:
                r_token = token
            else:
                r_token = expired_token

            return r_token, None, None, True, r_token.uploaded

        time_alive = (datetime.now(timezone.utc) - token.created_at).total_seconds()

        time_left = None

        # If the active token is alive for less than 60 seconds, use it.
        if time_alive < 60:
            time_left = 60 - time_alive

        # If the active token is alive for more than 60 and less than
        # 70 seconds, it is considered the currently expired token.
        elif time_alive < 70:
            token.expired = True
            token.save()
            expired_token = token

            # A new, active token must be created.
            token = IDToken.objects.create(user=user)
            time_left = 60

        # If the active token is alive for more than 70 seconds, it isn't valid anymore.
        # A new one must be created and used.
        else:
            token.delete()
            token = None
            token = IDToken.objects.create(user=user)
            time_left = 60

        return token, time_left, expired_token, False, None


class IDTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        token, time_left, expired_token, called, uploaded = refresh_token_validity(request.user)

        if not called:
            response = {
                'token': str(token.token),
                'expired_token': str(expired_token.token) if expired_token else None,
                'time_left': time_left
            }
        else:
            response = {
                'token': str(token.token),
                'expired_token': None,
                'time_left': None,
                'called': True,
                'uploaded': uploaded
            }

        return Response(response)


class CallToken(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')

        if not IDToken.objects.filter(token=token).exists():
            return Response(
                {'TokenNotFound': 'Given token was not found or is not valid anymore.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, time_left, expired, token.called, token.uploaded = refresh_token_validity(token=token)

        if token:
            token.called = True
            token.save()

            return Response(
                {'success': 'The token has been called.'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'TokenNotFound': 'Given token was not found or is not valid anymore.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ProgressReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if IDToken.objects.filter(user=request.user, token=request.data.get('token'), called=True).exists():
            token = IDToken.objects.get(token=request.data.get('token'))

            data = {
                'called': True,
                'uploaded': token.uploaded
            }

            if token.uploaded is True:
                token.delete()

            return Response(data)

        return Response(
                {'TokenNotFound': 'Given token not found or not associated with authenticated user.'},
                status=status.HTTP_400_BAD_REQUEST
            )
