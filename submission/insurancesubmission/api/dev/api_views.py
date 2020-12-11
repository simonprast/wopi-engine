#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import json

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response

from submission.insurancesubmission.models import InsuranceSubmission

from user.api.dev.serializers import LoginUserSerializer, UserDetailSerializer
from user.create_or_login import create_or_login

from .serializers import InsuranceSubmissionSerializer


class SubmitInsurance(generics.GenericAPIView):
    serializer_class = InsuranceSubmissionSerializer
    permission_classes = [permissions.AllowAny]

    # POST a new insurance submission either through registration or through normal usage (user)
    def post(self, request, *args, **kwargs):
        # For anonymous users, an account will be created with the insurance submission process
        if request.user.is_anonymous:
            # Both the UserDetailSerializer and the SubmitSerializer are used
            register_serializer = UserDetailSerializer(data=request.data)
            login_serializer = LoginUserSerializer(data=request.data)
            submit_serializer = InsuranceSubmissionSerializer(
                data=request.data)

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
            serializer = InsuranceSubmissionSerializer(data=request.data)

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


class GetInsuranceSubmissions(generics.GenericAPIView):
    queryset = InsuranceSubmission.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_user_submissions(self, user):
        try:
            submissions = InsuranceSubmission.objects.filter(
                submitter=user, denied=False)
            return submissions
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def get_admin_submissions(self, denied=None):
        try:
            if denied is False or denied is True:
                submissions = InsuranceSubmission.objects.filter(denied=denied)
            else:
                submissions = InsuranceSubmission.objects.all()
            return submissions
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def create_submission_list(self, submissions):
        submission_list = []
        for submission in submissions:
            submission_obj = {
                'id': submission.id,
                'insurance': str(submission.insurance),
                'policy_id': submission.policy_id,
                'submitter': str(submission.submitter),
                'status': {
                    'active': submission.active,
                    'denied': submission.denied
                },
                'data': json.loads((submission.data).replace("\'", "\""))
            }

            submission_list.append(submission_obj)

        return submission_list

    def get(self, request, *args, **kwargs):
        # A staff user is allowed to see all submissions
        if request.user.is_staff:
            submissions = self.get_admin_submissions()
        # AnonymousUsers are denied.
        # If the User is not anonymous, only show submissions of the requesting users.
        else:
            submissions = self.get_user_submissions(user=request.user)

        submission_list = self.create_submission_list(submissions)
        return Response(submission_list, status=status.HTTP_200_OK)
