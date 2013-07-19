from django.conf import settings

from baph.utils.module_loading import import_by_path

UNUSABLE_PASSWORD_PREFIX = '!'  # This will never be a valid encoded hash
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40  # number of random chars to add after UNUSABLE_PASSWORD_PREFIX
HASHERS = None  # lazily loaded from PASSWORD_HASHERS
PREFERRED_HASHER = None  # defaults to first item in PASSWORD_HASHERS


def get_hasher(algorithm='default'):
    """
    Returns an instance of a loaded password hasher.

    If algorithm is 'default', the default hasher will be returned.
    This function will also lazy import hashers specified in your
    settings file if needed.
    """
    if hasattr(algorithm, 'algorithm'):
        return algorithm

    elif algorithm == 'default':
        if PREFERRED_HASHER is None:
            load_hashers()
        return PREFERRED_HASHER
    else:
        if HASHERS is None:
            load_hashers()
        if algorithm not in HASHERS:
            raise ValueError("Unknown password hashing algorithm '%s'. "
                             "Did you specify it in the PASSWORD_HASHERS "
                             "setting?" % algorithm)
        return HASHERS[algorithm]

def identify_hasher(encoded):
    """
    Returns an instance of a loaded password hasher.

    Identifies hasher algorithm by examining encoded hash, and calls
    get_hasher() to return hasher. Raises ValueError if
    algorithm cannot be identified, or if hasher is not loaded.
    """
    # Ancient versions of Django created plain MD5 passwords and accepted
    # MD5 passwords with an empty salt.
    if ((len(encoded) == 32 and '$' not in encoded) or
            (len(encoded) == 37 and encoded.startswith('md5$$'))):
        algorithm = 'unsalted_md5'
    # Ancient versions of Django accepted SHA1 passwords with an empty salt.
    elif len(encoded) == 46 and encoded.startswith('sha1$$'):
        algorithm = 'unsalted_sha1'
    else:
        algorithm = encoded.split('$', 1)[0]
    return get_hasher(algorithm)

def is_password_usable(encoded):
    if encoded is None or encoded.startswith(UNUSABLE_PASSWORD_PREFIX):
        return False
    try:
        identify_hasher(encoded)
    except ValueError:
        return False
    return True

def check_password(password, encoded, setter=None, preferred='default'):
    """
    Returns a boolean of whether the raw password matches the three
    part encoded digest.

    If setter is specified, it'll be called when you need to
    regenerate the password.
    """
    if not password or not is_password_usable(encoded):
        return False

    #preferred = get_hasher(preferred)
    hasher = identify_hasher(encoded)

    #must_update = hasher.algorithm != preferred.algorithm
    is_correct = hasher.verify(password, encoded)
    #if setter and is_correct and must_update:
    #    setter(password)
    return is_correct



def load_hashers(password_hashers=None):
    global HASHERS
    global PREFERRED_HASHER
    hashers = []
    if not password_hashers:
        password_hashers = settings.PASSWORD_HASHERS
    for backend in password_hashers:
        hasher = import_by_path(backend)()
        if not getattr(hasher, 'algorithm'):
            raise ImproperlyConfigured("hasher doesn't specify an "
                                       "algorithm name: %s" % backend)
        hashers.append(hasher)
    HASHERS = dict([(hasher.algorithm, hasher) for hasher in hashers])
    PREFERRED_HASHER = hashers[0]

def make_password(password, salt=None, hasher='default'):
    """
    Turn a plain-text password into a hash for database storage

    Same as encode() but generates a new random salt.  If
    password is None or blank then UNUSABLE_PASSWORD will be
    returned which disallows logins.
    """
    if not password:
        return UNUSABLE_PASSWORD

    hasher = get_hasher(hasher)

    if not salt:
        salt = hasher.salt()

    return hasher.encode(password, salt)

