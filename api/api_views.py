#
# Created on Mon Nov 02 2020
#
# Copyright (c) 2020 - Simon Prast
#


from django.conf import settings
from django.http import JsonResponse


# Return the current LTS API version defined at settings.VERSION
def show_version(request):
    if request.method == 'GET':
        return JsonResponse({'version': settings.VERSION})
