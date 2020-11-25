#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .serializers import SubmitSerializer, RegisterSubmitSerializer


class Submit(generics.GenericAPIView):
    serializer_class = SubmitSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            serializer = RegisterSubmitSerializer(data=request.data)

            if not serializer.is_valid():
                # Return the serializer errors in case the request validation fails
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Save the submission through the serializer
                submission = serializer.save()

                # If the serializer.save() method returns the string 'DuplicateError', it means that a
                # submission with the exact same submission data already exists for this insurance.
                # In this case, the submission is not saved.
                if submission == 'DuplicateError':
                    return Response({'DuplicateError': 'An identical submission already exists.'},
                                    status=status.HTTP_403_FORBIDDEN)

                return Response({'success': str(submission)}, status=status.HTTP_201_CREATED)
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
