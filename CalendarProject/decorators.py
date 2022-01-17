from django.core.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist

import jwt
from django.conf import settings
from datetime import date, datetime, timedelta


def contains_jwt(function):
    def _inner(request, *args, **kwargs):

        user = request.user

        try:
            token = user.token
        except AttributeError:
            raise PermissionDenied('Not logged in')

        try:
            payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms=['HS256', ])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise PermissionDenied('Token invalid')

        if datetime.timestamp(datetime.now()) >= payload['exp']:
            raise PermissionDenied('Token expired')

        return function(request, *args, **kwargs)

    return _inner
