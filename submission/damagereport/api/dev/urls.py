#
# Created on Wed Nov 18 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # POST - create new damage report (customer)
    path('submit/', api_views.SubmitDamageReport.as_view()),

    # POST - send message to a damage report (customer/admin)
    path('submit/<int:report>/', api_views.SendMessage.as_view()),

    # POST - change a damage report's status from o/w to c or back to w (admin)
    path('close/<int:report>/', api_views.OpenCloseDamageReport.as_view()),

    # GET - show all own damage reports o/w/c (customer)
    # GET - show damage reports of related users (admin)
    path('show/', api_views.GetDamageReports.as_view()),

    # GET - show all damage reports o/w/c + denied (admin)
    path('show/all/', api_views.GetAllDamageReports.as_view()),

    # GET - show all messages of as specific damage report (customer/admin)
    path('show/<int:pk>/', api_views.GetDamageReportDetails.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
