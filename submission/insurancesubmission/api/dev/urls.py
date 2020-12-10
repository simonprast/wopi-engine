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

    # GET - show all own insurance policies and submissions which are not denied (customer)
    # GET - show all insurance submissions (admin)
    path('show/', api_views.GetInsuranceSubmissions.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
