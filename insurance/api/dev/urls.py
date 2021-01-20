from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST - request to calculate policy with given insurance data
    path('', api_views.CalculateInsurance.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
