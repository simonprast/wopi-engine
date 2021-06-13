#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#

import base64
import json
import imghdr
import os

from datetime import datetime, timezone

from django.conf import settings
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response

from submission.insurancesubmission.insert_pdf_data import insert_payment_data, insert_signature
from submission.insurancesubmission.models import InsuranceSubmission, Document, DocumentToken
from submission.insurancesubmission.create_insurance_pdf import create_pdf


from user.api.dev.serializers import LoginUserSerializer, UserDetailSerializer
from user.create_or_login import create_or_login

# from .permissions import HasTokenOrIsAuthenticated
from .serializers import InsuranceSubmissionSerializer, DocumentSerializer


class SubmitInsurance(generics.GenericAPIView):
    serializer_class = InsuranceSubmissionSerializer
    permission_classes = [permissions.AllowAny]

    # POST a new insurance submission either through registration or through normal usage (user)
    def post(self, request, *args, **kwargs):
        # For anonymous users, an account will be created with the insurance submission process
        if request.user.is_anonymous:
            # Both the UserDetailSerializer and the InsuranceSubmissionSerializer are used
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

            create_pdf(request, submission)

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

                create_pdf(request, submission)
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
            documents = Document.objects.filter(insurance_submission=submission)
            serializer = DocumentSerializer(documents, many=True)
            submission_obj = {
                'id': submission.id,
                'insurance': str(submission.insurance),
                'date': str(submission.datetime),
                'policy_id': submission.policy_id,
                'submitter': str(submission.submitter),
                'status': {
                    'active': submission.active,
                    'denied': submission.denied,
                    'status': submission.status
                },
                'document': None if not submission.policy_document else submission.policy_document.url,
                'submission_documents': None if len(documents) == 0 else serializer.data,
                'data': json.loads((submission.data).replace("\'", "\"")),
                'options': json.loads(translate_options())
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


class ChangeInsuranceSubmissionDetails(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get_submission(self, pk):
        try:
            submissions = InsuranceSubmission.objects.get(pk=pk)
            return submissions
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def put(self, request, pk, *args, **kwargs):
        # Get the requested submission
        submission = self.get_submission(pk=pk)

        if request.data.__contains__('active'):
            active = True if request.data.get(
                'active').lower() == 'true' else False
            submission.active = active

        if request.data.__contains__('denied'):
            denied = True if request.data.get(
                'denied').lower() == 'true' else False
            submission.denied = denied

        if request.data.__contains__('policy_id'):
            if len(request.data.get('policy_id')) > 64:
                return Response({'policy_id': 'The maximum length is 64 characters.'})

            submission.policy_id = request.data.get('policy_id')

        if (request.data.__contains__('document')
                and (type(request.data.get('document')) is InMemoryUploadedFile
                     or type(request.data.get('document')) is TemporaryUploadedFile)):
            submission.policy_document = request.data.get('document')
            submission.active = True

        submission.save()

        return Response(
            {
                'policy_id': submission.policy_id,
                'document': None if not submission.policy_document else submission.policy_document.url,
                'active': submission.active,
                'denied': submission.denied,
            }, status=status.HTTP_200_OK
        )


class AddTemplateDocument(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get_submission(self, pk):
        try:
            submissions = InsuranceSubmission.objects.get(pk=pk)
            return submissions
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def get_document(self, pk):
        try:
            document = Document.objects.get(pk=pk)
            return document
        except Document.DoesNotExist:
            raise exceptions.NotFound

    def post(self, request, pk, *args, **kwargs):
        # Get the requested submission
        submission = self.get_submission(pk=pk)
        pos_x = request.data.get('pos_x')
        pos_y = request.data.get('pos_y')
        page_index = request.data.get('page_index')

        if submission.active:
            raise exceptions.ValidationError({'error': 'You cannot change agreement files on active contracts.'})

        if request.data.get('id'):
            document = self.get_document(request.data.get('id'))

            if request.data.get('title'):
                document.title = request.data.get('title')

            if request.data.get('description'):
                document.description = request.data.get('description')

            document.save()
        elif request.data.get('remove'):
            document = self.get_document(request.data.get('remove'))
            document.delete()
            return Response({'success': 'Successfully deleted document with id ' + request.data.get('remove') + '.'})
        else:
            document = Document.objects.create(
                insurance_submission=submission,
                title=request.data.get('title'),
                description=request.data.get('description')
            )

        if (request.data.__contains__('template')
                and (type(request.data.get('template')) is InMemoryUploadedFile
                     or type(request.data.get('template')) is TemporaryUploadedFile)):
            document.template = request.data.get('template')

        if pos_x and pos_y:
            document.pos_x = pos_x
            document.pos_y = pos_y

        if page_index:
            document.page_index = page_index

        document.save()

        submission.status = 'o'
        submission.save()

        documents = Document.objects.filter(insurance_submission=submission)
        serializer = DocumentSerializer(documents, many=True)

        return Response(
            {
                'submission_id': submission.id,
                'documents': None if documents.__len__ == 0 else serializer.data,
                'active': submission.active,
                'denied': submission.denied,
            }, status=status.HTTP_200_OK
        )


class RequestSignSubmission(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self, pk):
        try:
            submission = InsuranceSubmission.objects.get(pk=pk)
            return submission
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def get(self, request, pk, *args, **kwargs):
        submission = self.get_submission(pk=pk)

        documents = Document.objects.filter(insurance_submission=submission)

        token, time_left, expired_token, called, signed = refresh_token_validity(request.user, documents[0])

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
                'signed': signed
            }

        return Response(response)


def refresh_token_validity(user=None, document=None, token=None, force=None):
    if user and token:
        raise exceptions.ValidationError({'error': 'You cannot provide user and token value.'})

    # Check a specific token.
    if token:
        if DocumentToken.objects.filter(token=token).exists():
            token = DocumentToken.objects.get(token=token)

            # Get the user to whom the given token belongs to.
            user = token.user

    if force:
        DocumentToken.objects.filter(user=user).delete()

    # Initialize variable.
    expired_token = None

    if DocumentToken.objects.filter(user=user).exists():
        tokens = DocumentToken.objects.filter(user=user)

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
        token = DocumentToken.objects.create(user=user, document=document)

    # At this point, we've got the user of a token

    if token.document != document:
        token.delete()

    if expired_token and expired_token.document != document:
        expired_token.delete()

    # Initialize variable.
    called = False

    e_called = expired_token.called if expired_token else False

    if token.called or e_called:
        if token.called:
            r_token = token
        else:
            r_token = expired_token

        time_alive = (datetime.now(timezone.utc) - r_token.created_at).total_seconds()

        if time_alive < 1800:
            time_left = 1800 - time_alive
            called = True

            return r_token, None, None, called, r_token.signed
        else:
            r_token.delete()
            token = DocumentToken.objects.create(user=user, document=document)

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
        token = DocumentToken.objects.create(user=user, document=document)
        time_left = 60

    # If the active token is alive for more than 70 seconds, it isn't valid anymore.
    # A new one must be created and used.
    else:
        token.delete()
        token = None
        token = DocumentToken.objects.create(user=user, document=document)
        time_left = 60

    return token, time_left, expired_token, False, None


class RequestSignDocument(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_document(self, pk):
        try:
            document = Document.objects.get(pk=pk)
            return document
        except Document.DoesNotExist:
            raise exceptions.NotFound

    def post(self, request, pk, *args, **kwargs):
        # The document which should be signed.
        document = self.get_document(pk=pk)

        # If force is of true value, a new token will be forced even if a called token did already exist.
        force = request.data.get('force')

        # The user to which the tokens will be assigned.
        user = document.insurance_submission.submitter

        token, time_left, expired_token, called, uploaded = refresh_token_validity(
            user=user, document=document, force=force)

        document_data = {
            'id': document.id,
            'title': document.title,
            'description': document.description,
            'template': document.template.url if document.template else None,
            'document': document.document.url if document.document else None,
            'signature': document.signature.url if document.signature else None,
            'pos_x': document.pos_x,
            'pos_y': document.pos_y,
            'page_index': document.page_index
        }

        if not called:
            response = {
                'document': document_data,
                'token': str(token.token),
                'expired_token': str(expired_token.token) if expired_token else None,
                'time_left': time_left
            }
        else:
            response = {
                'document': document_data,
                'token': str(token.token),
                'expired_token': None,
                'time_left': None,
                'called': True,
                'signed': token.signed
            }

        return Response(response)


class CallDocumentToken(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')

        if not DocumentToken.objects.filter(token=token).exists():
            return Response(
                {'TokenNotFound': 'Given token was not found or is not valid anymore.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token, time_left, expired, token.called, token.uploaded = refresh_token_validity(token=token)

        if token:
            token.called = True
            token.save()

            document = token.document
            document_data = {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'template': document.template.url if document.template else None,
                'document': document.document.url if document.document else None,
                'signature': document.signature.url if document.signature else None,
                'pos_x': document.pos_x,
                'pos_y': document.pos_y,
                'page_index': document.page_index
            }

            return Response(
                {
                    'success': 'The token has been called.',
                    'document': document_data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {'TokenNotFound': 'Given token was not found or is not valid anymore.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ProgressReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if DocumentToken.objects.filter(user=request.user, called=True).exists():
            token = DocumentToken.objects.get(user=request.user, called=True)

            document = token.document
            document_data = {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'template': document.template.url if document.template else None,
                'document': document.document.url if document.document else None,
                'signature': document.signature.url if document.signature else None,
                'pos_x': document.pos_x,
                'pos_y': document.pos_y,
                'page_index': document.page_index
            }

            data = {
                'document': document_data,
                'called': token.called,
                'signed': token.signed
            }

            if token.signed:
                token.delete()

            return Response(data)

        return Response(
                {'TokenNotFound': 'Given token not found or not associated with authenticated user.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SignDocument(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get_document(self, token):
        try:
            document_token = DocumentToken.objects.get(token=token, called=True)
            return document_token.document
        except Document.DoesNotExist:
            raise exceptions.NotFound

    def get_token(self, token):
        try:
            document_token = DocumentToken.objects.get(token=token, called=True)
            return document_token
        except DocumentToken.DoesNotExist:
            raise exceptions.NotFound

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        signature = request.data.get('signature')
        document = self.get_document(token=token)

        if not signature:
            raise exceptions.ValidationError({'signature': 'Please provide a valid image file for this field.'})

        signature = signature[22:]
        signature = base64.b64decode(signature)

        image_path = os.path.join(settings.MEDIA_ROOT, "tmp")

        if not os.path.exists(image_path):
            os.makedirs(image_path)

        image = open(image_path + "/image.png", "wb")
        image.write(signature)
        image.close()

        with open(image_path + "/image.png", "rb") as f:
            image = File(f)

            if imghdr.what(image) is None:
                return Response(
                    {
                        'error': [
                            'InvalidSignatureFile',
                            'Signature seems to be not a valid image file.'
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not token and not request.user.is_authenticated:
                raise exceptions.PermissionDenied

            token_object = None

            if token:
                token_object = self.get_token(token=token)
                # Check token validitiy here
                user = token_object.user
            elif request.user.is_authenticated:
                user = request.user

            if document.insurance_submission.submitter != user:
                raise exceptions.PermissionDenied

            document.signature = image
            document.save()

            insert_signature(document)

            if token_object:
                token_object.signed = True
                token_object.save()

            document_data = {
                'id': document.id,
                'title': document.title,
                'description': document.description,
                'template': document.template.url if document.template else None,
                'document': document.document.url if document.document else None,
                'signature': document.signature.url if document.signature else None,
                'pos_x': document.pos_x,
                'pos_y': document.pos_y,
                'page_index': document.page_index
            }

            return Response({
                'document': document_data
            })


# class AddSubmissionDocument(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get_submission(self, pk):
#         try:
#             submission = InsuranceSubmission.objects.get(pk=pk)
#             return submission
#         except InsuranceSubmission.DoesNotExist:
#             raise exceptions.NotFound

#     def post(self, request, pk, *args, **kwargs):
#         # Get the requested submission
#         submission = self.get_submission(pk=pk)

#         if not submission.submitter == request.user and not request.user.is_staff:
#             raise exceptions.PermissionDenied

#         if submission.active:
#             return Response({'error': 'You cannot change agreement files on active contracts.'})

#         if request.data.__contains__('id'):
#             document = Document.objects.get(pk=request.data.get('id'))
#             if (request.data.__contains__('document')
#                 and (type(request.data.get('document')) is InMemoryUploadedFile
#                      or type(request.data.get('document')) is TemporaryUploadedFile)):
#                 document.document = request.data.get('document')
#                 document.save()
#         else:
#             return Response('Request must contain document id.', status=status.HTTP_400_BAD_REQUEST)

#         submission.status = 'w'
#         submission.save()

#         documents = Document.objects.filter(insurance_submission=submission)
#         serializer = DocumentSerializer(documents, many=True)

#         return Response(
#             {
#                 'policy_id': submission.policy_id,
#                 'documents': None if documents.__len__ == 0 else serializer.data,
#                 'active': submission.active,
#                 'denied': submission.denied,
#             }, status=status.HTTP_200_OK
#         )


class AddPaymentData(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self, pk):
        try:
            submission = InsuranceSubmission.objects.get(pk=pk)
            return submission
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def post(self, request, pk, *args, **kwargs):
        # Get the requested submission
        submission = self.get_submission(pk=pk)

        if not submission.submitter == request.user and not request.user.is_staff:
            raise exceptions.PermissionDenied

        if submission.active:
            raise exceptions.ValidationError({'error': 'You cannot change agreement files on active contracts.'})

        iban = request.data.get('iban')
        bic = request.data.get('bic')

        if not iban:
            raise exceptions.ValidationError({'iban': 'This field is required.'})

        provider_id = 'ws'

        if provider_id == 'ws' and not bic:
            raise exceptions.ValidationError({'bic': 'This field is required for insurance WS.'})

        title = 'Lastschriftverfahren ' + submission.submitter.first_name + ' ' + submission.submitter.last_name

        document = Document.objects.create(
            title=title,
            description='SEPA-Lastschriftverfahren',
            insurance_submission=submission
        )

        user = submission.submitter

        if provider_id:
            if provider_id == 'vav':
                # data coordinates in mm
                vav_co = {
                    'full_name': [64, 71.5],
                    'first_name': [64, 120.5],
                    'last_name': [64, 128.64],
                    'street': [64, 136.78],
                    'street_number': [64, 144.92],
                    'zipcode': [64, 153.06],
                    'city': [64, 161.2],
                    'country': [64, 169.34],
                    'birthdate': [64, 177.48],
                    'iban': [64, 185.62]
                }

                coordinates = vav_co

                data = {
                    'full_name': user.first_name + ' ' + user.last_name,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'street': user.address_1,
                    'street_number': user.address_1,
                    'zipcode': user.zipcode,
                    'city': user.zipcode,
                    'country': 'Österreich',
                    'birthdate': str(user.birthdate),
                    'iban': iban
                }
            elif provider_id == 'ws':
                # data coordinates in mm
                ws_co = {
                    'last_name': [25, 168],
                    'first_name': [102.5, 168],
                    'address': [25, 183],
                    'zip_city': [25, 198],
                    'iban': [34, 222.5],
                    'bic': [34, 237.5]
                }

                data = {
                    'last_name': user.last_name,
                    'first_name': user.first_name,
                    'address': user.address_1,
                    'zip_city': str(user.zipcode) + ' ' + str(user.zipcode),
                    'iban': iban,
                    'bic': bic
                }

                coordinates = ws_co
        else:
            raise exceptions.ValidationError({
                'error': 'Provider id is not able to create payment data sheet. Submission pID: ' + str(provider_id)
            })

        # Create a file for the Django FileField
        template = open('static/' + provider_id + '-template.pdf', 'rb')
        template_djangofile = File(template)
        document.template.save(title + '.pdf', template_djangofile)
        template.close()

        insert_payment_data(document, data, coordinates)

        return Response({'success': True})


def translate_options():
    options = '''
    [
        {
            "field_name": "hhv_zonenfaktor",
            "field_type": "integer",
            "options": {
                "1": "Zone 1",
                "2": "Zone 2",
                "3": "Zone 3",
                "4": "Zone 4",
                "5": "Zone 5"
            }
        },
        {
            "field_name": "staendigbewohnt",
            "field_type": "integer",
            "options": {
                "0": "Das Gebäude ist weniger als 9 Monate im Jahr bewohnt.",
                "1": "Das Gebäude ist mehr als 9 Monate im Jahr bewohnt."
            }
        },
        {
            "field_name": "schwimmbecken",
            "field_type": "integer",
            "options": {
                "0": "Kein Schwimmbecken mitversichern",
                "1": "Schwimmbecken + Abdeckung mitversichern",
                "2": "Schwimmbecken + Abdeckung + Technik mitversichern "
            }
        },
        {
            "field_name": "alarmanlage",
            "field_type": "integer",
            "options": {
                "0": "Keine Alarmanlage",
                "1": "Alarmanlage vorhanden"
            }
        },
        {
            "field_name": "sicherheitstuer",
            "field_type": "integer",
            "options": {
                "0": "Keine Sicherheitstür",
                "1": "Sicherheitstür vorhanden"
            }
        },
        {
            "field_name": "selbstbehaltsnachlass",
            "field_type": "integer",
            "options": {
                "0": "Kein Selbstbehalt",
                "1": "Nachlass-Stufe 1: 100€-150€ SB / 10%",
                "2": "Nachlass-Stufe 2: 200€-300€ SB / 20%",
                "3": "Nachlass-Stufe 3: 400€-500€ SB / 30%"
            }
        },
        {
            "field_name": "publicworker",
            "field_type": "integer",
            "options": {
                "0": "Kein Angestellter des öffentlichen Dienstes",
                "1": "Angestellter des öffentlichen Dienstes"
            }
        },
        {
            "field_name": "vavmehrspartenbonus",
            "field_type": "integer",
            "options": {
                "0": "Kein VAV Kunde",
                "1": "Bestehender VAV Kunde"
            }
        },
        {
            "field_name": "shortterm",
            "field_title": "Verkürzte 5- oder 3-jährige Laufzeit",
            "field_type": "integer",
            "options": {
                "0": "Keine verkürzte Laufzeit",
                "1": "5-jährige Laufzeit gewünscht",
                "2": "3-jährige Laufzeit gewünscht"
            }
        },
        {
            "field_name": "extrasecurity",
            "field_title": "Brandmeldeanlage mit Direktschaltung zur Feuerwehr, ..",
            "field_type": "integer",
            "options": {
                "0": "Extra Sicherheitsmaßnahmen vorhanden (Brandmeldeanlage mit Direktschaltung zur Feuerwehr, ..)",
                "1": "Keine extra Sicherheitsmaßnahmen vorhanden"
            }
        },
        {
            "field_name": "smarthomesecurity",
            "field_title": "Smarthome Sicherheitstechnik vorhanden? (Anschluss an Sicherheitszentrale)",
            "field_type": "integer",
            "options": {
                "1": "Smarthome Sicherheitstechnik vorhanden",
                "2": "Keine Smarthome Sicherheitstechnik"
            }
        },
        {
            "field_name": "glas",
            "field_type": "integer",
            "options": {
                "0": "Glasbruch soll mitversichert werden",
                "1": "Auf Glasbruch kann auch verzichtet werden"
            }
        },
        {
            "field_name": "zweitein",
            "field_type": "integer",
            "options": {
                "0": "Kein Zweitwohnsitz oder Einpersonenhaushalt",
                "1": "Zweitwohnsitz oder Einpersonenhaushalt"
            }
        },
        {
            "field_name": "regionalrabatt",
            "field_type": "string",
            "options": {
                "wien": "Wien",
                "niederoesterreich": "Niederoesterreich",
                "steiermark": "Steiermark",
                "burgenland": "Burgenland",
                "oberoesterreich": "Oberösterreich",
                "kaernten": "Kärnten",
                "salzburg": "Salzburg",
                "tirol": "Tirol",
                "vorarlberg": "Vorarlberg"
            }
        }
    ]
    '''

    return options
