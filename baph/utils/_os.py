import sys

import six


if six.PY2:
    fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()

def upath(path):
  """
  Always return a unicode path.
  """
  if six.PY2 and not isinstance(path, six.text_type):
    return path.decode(fs_encoding)
  return path

def npath(path):
  """
  Always return a native path, that is unicode on Python 3 and bytestring on
  Python 2.
  """
  if six.PY2 and not isinstance(path, bytes):
    return path.encode(fs_encoding)
  return path