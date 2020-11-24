#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path, include


urlpatterns = [
    path('users/', include('user.api.dev.urls')),
]
