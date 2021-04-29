#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST - request new insurance policy and create user account (customer)
    # POST - request new insurance policy (customer)
    path('submit/', api_views.SubmitInsurance.as_view()),

    # GET - request the signature of all documents of one submission (customer)
    path('sign/submission/<int:pk>/request/', api_views.RequestSignSubmission.as_view()),

    # GET - request the signature of a specific document of one submission,
    # following the remaining of the documents (customer)
    path('sign/document/<int:pk>/request/', api_views.RequestSignDocument.as_view()),

    # POST - Call the given token on the mobile device (customer)
    path('sign/document/<int:pk>/call/', api_views.CallDocumentToken.as_view()),

    # GET - Get a token's current progress (customer)
    path('sign/document/<int:pk>/progress/', api_views.ProgressReportView.as_view()),

    # POST - Add the signature file (customer)
    path('sign/document/<int:pk>/signature/', api_views.SignDocument.as_view()),

    # POST - add blank template agreement/contract documents (admin)
    path('submit/<int:pk>/template/', api_views.AddTemplateDocument.as_view()),

    # POST - add signed insurance agreement (customer)
    path('submit/<int:pk>/agreement/', api_views.AddSubmissionDocument.as_view()),

    # GET - show all own insurance policies and submissions which are not denied (customer)
    # GET - show all insurance submissions (admin)
    path('show/', api_views.GetInsuranceSubmissions.as_view()),

    # PUT - change an insurance submission's details
    path('<int:pk>/change/', api_views.ChangeInsuranceSubmissionDetails.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
