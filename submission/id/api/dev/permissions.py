from rest_framework import permissions
from submission.id.models import IDToken


class HasTokenOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            if request.method == 'POST':
                print(request.data['token'])
                return IDToken.objects.filter(token=request.data['token']).exists()
            return False

        return request.user.IsAuthenticated
