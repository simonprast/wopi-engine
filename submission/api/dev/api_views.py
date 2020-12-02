#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response

from user.api.dev.serializers import LoginUserSerializer, RegisterUserSerializer
from user.create_or_login import create_or_login
from user.models import User

from submission.models import IDSubmission

from .serializers import SubmitSerializer, SubmitIDSerializer


class SubmitInsurance(generics.GenericAPIView):
    serializer_class = SubmitSerializer
    permission_classes = [permissions.AllowAny]

    # POST a new insurance submission either through registration or through normal usage (user)
    def post(self, request, *args, **kwargs):
        # For anonymous users, an account will be created with the insurance submission process
        if request.user.is_anonymous:
            # Both the RegisterUserSerializer and the SubmitSerializer are used
            register_serializer = RegisterUserSerializer(data=request.data)
            login_serializer = LoginUserSerializer(data=request.data)
            submit_serializer = SubmitSerializer(data=request.data)

            # Don't call them directly with 'with', as this does not execute the second method if the first one fails
            register_serializer_valid = register_serializer.is_valid()
            submit_serializer_valid = submit_serializer.is_valid()

            if not register_serializer_valid or not submit_serializer_valid:
                # Return both serializer errors if one fails
                # If one of them doesn't fail, their errors dict will be an empty dict
                return_dict = register_serializer.errors
                return_dict.update(submit_serializer.errors)
                return Response(return_dict, status.HTTP_400_BAD_REQUEST)

            # Using user.create_or_login.create_or_login(), create and
            # authenticate the user using the validated registration data.
            return_dict, auth_status, user = create_or_login(
                register_serializer, login_serializer, request, validated=True)

            # Save the submission through the serializer
            submission = submit_serializer.save(user=user)

            # If the serializer.save() method returns the string 'DuplicateError', it means that a
            # submission with the exact same submission data already exists for this insurance.
            # In this case, the submission is not saved.
            if submission == 'DuplicateError':
                return Response({'DuplicateError': 'An identical submission already exists.'},
                                status=status.HTTP_403_FORBIDDEN)

            # The endpoint returns the create_or_login return_dict containing authentication
            # info and appends the return string of the created submission on success.
            return_dict.update({'success': str(submission)})
            return Response(return_dict, status=status.HTTP_201_CREATED)
        else:
            serializer = SubmitSerializer(data=request.data)

            if not serializer.is_valid():
                # Return the serializer errors in case the request validation fails
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Save the submission through the serializer
                submission = serializer.save(user=request.user)

                # If the serializer.save() method returns the string 'DuplicateError', it means that a
                # submission with the exact same submission data already exists for this insurance.
                # In this case, the submission is not saved.
                if submission == 'DuplicateError':
                    return Response({'DuplicateError': 'An identical submission already exists.'},
                                    status=status.HTTP_403_FORBIDDEN)

                return Response({'success': str(submission)}, status=status.HTTP_201_CREATED)


class IDDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = SubmitIDSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, user, latest=True):
        try:
            submission = IDSubmission.objects.get(
                submission_submitter=user, latest=latest)
            return submission
        except IDSubmission.DoesNotExist:
            raise exceptions.NotFound

    # GET all latest, unverified ID documents (admin)
    # GET own, latest ID document and verified status (user)
    def get(self, request, *args, **kwargs):
        if request.user.is_staff:
            submissions = IDSubmission.objects.filter(
                verified=False, latest=True)
            serializer = SubmitIDSerializer(submissions, many=True)
            return Response(serializer.data)
        else:
            submission = self.get_object(user=request.user)
            serializer = SubmitIDSerializer(submission)
            return Response(serializer.data)

    # POST ID document (user)
    def post(self, request, *args, **kwargs):
        serializer = SubmitIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_document = serializer.save(user=request.user)
        return Response({'submission_id': str(id_document)})


class VerifyIDDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = SubmitIDSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, pk):
        try:
            submission = IDSubmission.objects.get(pk=pk)
            return submission
        except IDSubmission.DoesNotExist:
            raise exceptions.NotFound

    def put(self, request, pk, *args, **kwargs):
        submission = self.get_object(pk=pk)
        if request.data.__contains__('verified'):
            if request.data.__getitem__('verified').lower() in ('false', 'true'):
                verified = True if request.data.__getitem__(
                    'verified').lower() == 'true' else False
                if submission.verified is verified:
                    return Response({'verified': 'This ID has already given verified status.'})
                submission.verified = verified
                submission.save()
                return Response({'success': True, 'verified': verified, 'submission': str(submission)},
                                status=status.HTTP_200_OK)
            else:
                return Response(
                    {'verified': ['Value must be either True or False.']}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'verified': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'submission_id': 'ok'})


class UserIDDocument(generics.GenericAPIView):
    queryset = IDSubmission.objects.all()
    serializer_class = SubmitIDSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_user(self, pk):
        try:
            user = User.objects.get(pk=pk)
            return user
        except User.DoesNotExist:
            raise exceptions.NotFound

    # GET all ID documents of one user (admin)
    def get(self, request, pk, *args, **kwargs):
        user = self.get_user(pk=pk)
        submissions = IDSubmission.objects.filter(submission_submitter=user)
        serializer = SubmitIDSerializer(submissions, many=True)
        return Response(serializer.data)
