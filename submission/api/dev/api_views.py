#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from rest_framework import generics, permissions, status
from rest_framework.response import Response

# from submission.models import Submission

from .serializers import SubmitSerializer


class Submit(generics.GenericAPIView):
    serializer_class = SubmitSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            submission = serializer.save()
            if submission == 'DuplicateError':
                return Response({'DuplicateError': 'An identical submission already exists.'},
                                status=status.HTTP_403_FORBIDDEN)

            return Response({'success': str(submission)}, status=status.HTTP_201_CREATED)
