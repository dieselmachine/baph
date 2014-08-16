# -*- coding: utf-8 -*-
'''SQLAlchemy versions of :mod:`django.contrib.auth` utility functions.'''

from datetime import datetime
from django.contrib.auth import BACKEND_SESSION_KEY, load_backend, SESSION_KEY
from django.contrib.auth.models import AnonymousUser


def login(request, user):
    '''Persist a user id and a backend in the request. This way a user doesn't
    have to reauthenticate on every request.

    :param user: The user object.
    :type user: :class:`baph.contrib.auth.models.User`
    '''
    if hasattr(request, 'orm'):
        session = request.orm.sessionmaker()
    else:
        from .models import orm
        session = orm.sessionmaker()
    if user is None:
        user = request.user
    # TODO: It would be nice to support different login methods, like signed
    # cookies.
    user.last_login = datetime.now()
    session.commit()

    if SESSION_KEY in request.session:
        if request.session[SESSION_KEY] != user.id:
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()
        
    if hasattr(user, 'user_id'):
        # this is a split user model, with one auth record, and multiple user
        # records (one for each organization). Use the base user id for the 
        # identifier, and we'll grab the org-specific user via backend.get_user
        user_id = user.user_id
    else:
        user_id = user.id
        if hasattr(request, 'user'):
            request.user = user
    request.session[SESSION_KEY] = user_id
    request.session[BACKEND_SESSION_KEY] = user.backend


def logout(request):
    '''Removes the authenticated user's ID from the request and flushes their
    session data.
    '''
    request.session.flush()
    if hasattr(request, 'user'):
        from .models import AnonymousUser
        request.user = AnonymousUser()


def get_user(request):
    '''Retrieves the object representing the current user.'''
    from .models import AnonymousUser
    try:
        user_id = request.session[SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
        backend = load_backend(backend_path)
        if hasattr(request, 'org'):
            # Org middleware present- include org_id in filters
            org_id = getattr(request.org, 'id', None)
            user = backend.get_org_user(user_id, org_id) or AnonymousUser()
        else:
            user = backend.get_user(user_id) or AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user
