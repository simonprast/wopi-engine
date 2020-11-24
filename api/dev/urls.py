#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path, include


urlpatterns = [
    # This URLs file is routing the requests to each module's own URLs file
    path('users/', include('user.api.dev.urls')),
    path('submit/', include('submission.api.dev.urls'))
]
