# -*- coding: utf-8 -*-
from baph.db import Session
from django.http import Http404


def get_object_or_404(klass, **kwargs):
    session = kwargs.get('_session', Session())
    result = session.query(klass) \
                    .filter_by(**kwargs) \
                    .first()
    if result is None:
        raise Http404
    return result
