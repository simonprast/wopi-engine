#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST endpoint for submitting (and viewing) ID documents for both customers and admins
    path('document/', api_views.HandleDocument.as_view()),

    # PUT the verified value of an ID object
    path('verify/<int:pk>/', api_views.VerifyDocument.as_view()),

    # GET all IDs of a single user
    path('user/<int:pk>/', api_views.UserDocument.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
