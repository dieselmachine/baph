from __future__ import absolute_import

import json
from StringIO import StringIO

from baph.core.serializers.python import Serializer as PythonSerializer
from baph.core.serializers.python import Deserializer as PythonDeserializer
from django.core.serializers.json import DjangoJSONEncoder


class Serializer(PythonSerializer):
    """
    Convert a queryset to JSON.
    """
    internal_use_only = False

    def end_serialization(self):
        json.dump(self.objects, self.stream, cls=DjangoJSONEncoder,
            **self.options)

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    for obj in PythonDeserializer(json.load(stream), **options):
        yield obj
