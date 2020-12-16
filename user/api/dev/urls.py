#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.urlpatterns import format_suffix_patterns

from . import api_views

urlpatterns = [
    # GET - show the requesting user itself (customer/admin)
    # GET - show a list of all users, staff as well as customers (admin)
    path('', api_views.UserList.as_view()),

    # GET - show details of a specific user (admin)
    # GET - show details of a specific user (customer - if the requested user is the customer itself)
    # PUT - change a specific user's data (admin)
    # PUT - change a specific user's data (customer - if the requsted user is the customer itself)
    path('<uuid:pk>/', api_views.UserDetail.as_view()),

    # POST - create a new user or authenticate an existing user
    path('create/', api_views.UserCreateOrLogin.as_view()),

    # POST - verify a customer's email address using a token
    path('verify-mail/<uuid:token>/', api_views.VerifyEmail.as_view()),

    # POST - request a verification token for the current email address
    path('verify-mail/request/', api_views.RequestEmailVerification.as_view()),

    # POST - change a user's password using a token
    path('password/reset/<uuid:token>/', api_views.ResetPassword.as_view()),

    # POST - request a password reset token to be sent to the user's email address
    path('password/request/', api_views.RequestPasswordReset.as_view()),

    # Todo:
    # https://stackoverflow.com/questions/14567586/token-authentication-for-restful-api-should-the-token-be-periodically-changed
    path('auth/', obtain_auth_token, name='api_token_auth'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
