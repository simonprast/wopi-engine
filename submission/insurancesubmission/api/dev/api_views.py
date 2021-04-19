#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


import json

from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from rest_framework import exceptions, generics, permissions, status
from rest_framework.response import Response

from submission.insurancesubmission.models import InsuranceSubmission, Document

from user.api.dev.serializers import LoginUserSerializer, UserDetailSerializer
from user.create_or_login import create_or_login

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

        else:
            serializer = InsuranceSubmissionSerializer(data=request.data)

            if not serializer.is_valid():
                # Return the serializer errors in case the request validation fails
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Save the submission through the serializer
            submission = serializer.save(user=request.user)

        # If the serializer.save() method returns the string 'DuplicateError', it means that a
        # submission with the exact same submission data already exists for this insurance.
        # In this case, the submission is not saved.
        if submission == 'DuplicateError':
            return Response({'DuplicateError': 'An identical submission already exists.'},
                            status=status.HTTP_403_FORBIDDEN)

        titles = request.data.getlist('document_titles')
        descriptions = request.data.getlist('document_descriptions')
        templates = request.data.getlist('document_templates')
        documents = request.data.getlist('document_documents')
        if len(titles) == len(descriptions):
            for i in range(0, len(titles)):
                template, doc = None, None
                if len(templates) > i:
                    template=templates[i]
                if len(documents) > i:
                    doc=documents[i]
                document = Document.objects.create(
                    title=titles[i],
                    description=descriptions[i],
                    insurance_submission=submission,
                    template=template,
                    document=doc
                    )
                document.save()

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
                'submission_documents': None if documents.__len__ == 0 else serializer.data,
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

    def post(self, request, pk, *args, **kwargs):
        # Get the requested submission
        submission = self.get_submission(pk=pk)

        if submission.active:
            return Response({'error': 'You cannot change agreement files on active contracts.'})

        if request.data.__contains__('id'):
            document = Document.objects.get(pk=request.data.get('id'))
        else:
            document = Document.create(
                insurance_submission=submission,
                title=request.data.get('title'),
                description=request.data.get('description')
                )

        if (request.data.__contains__('template')
                and (type(request.data.get('template')) is InMemoryUploadedFile
                     or type(request.data.get('template')) is TemporaryUploadedFile)):
            document.template = request.data.get('template')
            document.save()

        submission.status = 'o'
        submission.save()

        documents = Document.objects.filter(insurance_submission=submission)
        serializer = DocumentSerializer(documents, many=True)
        return Response(
            {
                'policy_id': submission.policy_id,
                'documents': None if documents.__len__ == 0 else serializer.data,
                'active': submission.active,
                'denied': submission.denied,
            }, status=status.HTTP_200_OK
        )


class AddSubmissionDocument(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_submission(self, pk):
        try:
            submissions = InsuranceSubmission.objects.get(pk=pk)
            return submissions
        except InsuranceSubmission.DoesNotExist:
            raise exceptions.NotFound

    def post(self, request, pk, *args, **kwargs):
        # Get the requested submission
        submission = self.get_submission(pk=pk)

        if not submission.submitter == request.user and not request.user.is_staff:
            raise exceptions.PermissionDenied

        if submission.active:
            return Response({'error': 'You cannot change agreement files on active contracts.'})

        if request.data.__contains__('id'):
            document = Document.objects.get(pk=request.data.get('id'))
            if (request.data.__contains__('document')
                and (type(request.data.get('document')) is InMemoryUploadedFile
                        or type(request.data.get('document')) is TemporaryUploadedFile)):
                document.document = request.data.get('document')
                document.save()
        else:
            return Response('Request must contain document id.', status=status.HTTP_400_BAD_REQUEST)

        submission.status = 'w'
        submission.save()

        documents = Document.objects.filter(insurance_submission=submission)
        serializer = DocumentSerializer(documents, many=True)
        return Response(
            {
                'policy_id': submission.policy_id,
                'documents': None if documents.__len__ == 0 else serializer.data,
                'active': submission.active,
                'denied': submission.denied,
            }, status=status.HTTP_200_OK
        )


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
