#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST endpoint for submitting insurances and create a new customer account if needed
    path('submit/', api_views.SubmitInsurance.as_view()),
    path('show/', api_views.GetInsuranceSubmissions.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
