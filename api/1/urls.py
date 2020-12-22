#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path, include


urlpatterns = [
    # This URLs file is routing the requests to each module's own URLs file
    path('users/', include('user.api.1.urls')),
    path('damagereport/', include('submission.damagereport.api.1.urls')),
    path('id/', include('submission.id.api.1.urls')),
    path('insurance/', include('submission.insurancesubmission.api.1.urls')),
]
