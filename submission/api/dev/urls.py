#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    path('', api_views.Submit.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
