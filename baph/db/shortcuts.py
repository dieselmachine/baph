# -*- coding: utf-8 -*-
from django.http import Http404

from baph.db.orm import ORM

orm = ORM.get()


def get_object_or_404(klass, **kwargs):
    session = kwargs.get('_session', orm.sessionmaker())
    result = session.query(klass) \
                    .filter_by(**kwargs) \
                    .first()
    if result is None:
        raise Http404
    return result
