# copied from https://github.com/django/django/blob/master/django/core/serializers/base.py
"""
Module for abstract serializer/unserializer base classes.
"""

class SerializerDoesNotExist(KeyError):
    """The requested serializer was not found."""
    pass

class SerializationError(Exception):
    """Something bad happened during serialization."""
    pass

class DeserializationError(Exception):
    """Something bad happened during deserialization."""
    pass
