#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST endpoint for submitting insurances and ID documents
    path('', api_views.SubmitInsurance.as_view()),
    path('id/', api_views.IDDocument.as_view()),

    # PUT the verified value of an ID object
    path('id/verify/<int:pk>/', api_views.VerifyIDDocument.as_view()),

    # GET all IDs of a single user
    path('id/user/<int:pk>/', api_views.UserIDDocument.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
