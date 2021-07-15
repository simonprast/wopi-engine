#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


"""francy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db.utils import OperationalError
from django.urls import path, include
# from django.views.decorators.csrf import csrf_exempt

from user.models import create_admin_user
from api import api_views as main_api_views

# from insurance.tests import GenerateFile


urlpatterns = [
    path('admin/', admin.site.urls),

    # REST API

    # API versioning
    path('api/version', main_api_views.show_version),
    # Development version /api/dev/
    # Include all modules using API endpoints through the API module, not directly through the root URLs file.
    path('api/dev/', include('api.dev.urls')),

    # Please stick to the Semantic Versioning guidlines (semver.org) as good as possible.
    # Given a version number MAJOR.MINOR.PATCH, increment the:
    # - MAJOR version when you make incompatible API changes,
    # - MINOR version when you add functionality in a backwards compatible manner, and
    # - PATCH version when you make backwards compatible bug fixes.
    path('api/v1/', include('api.1.urls')),

    # path('pdftest', GenerateFile.as_view()),

    # path('api/v1/', include('user.api.v1.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

try:
    create_admin_user()
except OperationalError:
    print('COULD NOT CREATE ADMIN USER (is there an un-migrated field on the user model?)')
