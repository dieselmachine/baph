import datetime
import decimal
from StringIO import StringIO

from django.core.serializers.base import DeserializationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson

from baph.core.serializers.python import Serializer as PythonSerializer
from baph.core.serializers.python import Deserializer as PythonDeserializer


class Serializer(PythonSerializer):
    """
    Convert a queryset to JSON.
    """
    internal_use_only = False

    def end_serialization(self):
        if simplejson.__version__.split('.') >= ['2', '1', '3']:
            # Use JS strings to represent Python Decimal instances (ticket #16850)
            self.options.update({'use_decimal': False})
        simplejson.dump(self.objects, self.stream, cls=DjangoJSONEncoder,
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
    try:
        for obj in PythonDeserializer(simplejson.load(stream), **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception, e:
        # Map to deserializer error
        raise DeserializationError(e)
