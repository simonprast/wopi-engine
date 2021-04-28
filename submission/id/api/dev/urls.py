#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST - submit ID document (customer)
    # GET - shown own, latest ID document and verified status (customer)
    # GET - show all latest, unverified ID documents (admin)
    path('document/', api_views.HandleDocument.as_view()),

    # PUT - set verified field value of a specific ID object (admin)
    path('verify/<int:pk>/', api_views.VerifyDocument.as_view()),

    # GET - all IDs of a single user (admin)
    path('user/<uuid:pk>/', api_views.UserDocument.as_view()),

    # GET - Get or generate token for currently authenticated user (customer)
    path('user/idtoken/', api_views.IDTokenView.as_view()),

    # POST - Tell the server that a token has just been used on a mobile device
    path('user/idtoken/call/', api_views.CallToken.as_view()),

    # GET - Get the current progress of a token's lifespan, whether it has been called or used for uploading
    path('user/idtoken/progress/', api_views.ProgressReportView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
