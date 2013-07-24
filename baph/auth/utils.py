from hashlib import sha1
import datetime
import random
import types

from sqlalchemy import and_

from baph.db.orm import ORM


orm = ORM.get()

def has_perm(user, resource, action, filters={}):
    # TODO: remove this shim
    return user.has_perm(resource, action, filters)

def has_resource_perm(user, resource):
    # TODO: remove this shim
    return user.has_resource_perm(resource)

def build_filter_list(user, resource, action):
    '''
    builds a list of filters suitable for use in filter expressions
    eg: object_list.filter(or_(*filters))
    --params:
    user: user object for which to check permissions
    resource: name of the resource to check
    action: name of action to check permissions against
    '''
    perms = user.get_resource_permissions(resource, action)
    if not perms:
        return ['0=1']
    return perms_to_filters(perms)
    
def perms_to_filters(perms):
    formatted = []
    for p in perms:
        if not p.key:
            # this is a boolean permission (no filters involved)
            return []

        cls = orm.Base._decl_class_registry[p.base_class]
        keys = p.key.split(',')
        values = p.value.split(',')
        data = zip(keys, values)

        filters = []
        for key, value in data:
            frags = key.split('.')
            #cls = orm.Base._decl_class_registry[frags.pop(0)]
            attr = frags.pop()
            for frag in frags:
                rel = getattr(cls, frag)
                cls = rel.property.argument
                if isinstance(cls, types.FunctionType):
                    # lazy-loaded attr that hasn't been evaluated yet
                    cls = cls()
                if hasattr(cls, 'is_mapper') and cls.is_mapper:
                    # we found a mapper, grab the class from it
                    cls = cls.class_
            col = getattr(cls, attr)
            filters.append(col == value)

        if len(filters) == 1:
            formatted.append(filters[0])
        else:
            formatted.append(and_(*filters))
    return formatted

def generate_sha1(string, salt=None):
    """
    Generates a sha1 hash for supplied string. Doesn't need to be very secure
    because it's not used for password checking. We got Django for that.

    :param string:
        The string that needs to be encrypted.

    :param salt:
        Optionally define your own salt. If none is supplied, will use a random
        string of 5 characters.

    :return: Tuple containing the salt and hash.

    """
    if not salt:
        salt = sha1(str(random.random())).hexdigest()[:5]
    hash = sha1(salt+str(string)).hexdigest()

    return (salt, hash)

def get_datetime_now():
    """
    Returns datetime object with current point in time.

    In Django 1.4+ it uses Django's django.utils.timezone.now() which returns
    an aware or naive datetime that represents the current point in time
    when ``USE_TZ`` in project's settings is True or False respectively.
    In older versions of Django it uses datetime.datetime.now().

    """
    try:
        from baph.utils import timezone
        return timezone.now() # pragma: no cover
    except ImportError: # pragma: no cover
        return datetime.datetime.now().replace(microsecond=0)
