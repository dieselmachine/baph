# -*- coding: utf-8 -*-
from django.http import Http404


def get_object_or_404(cls, **kwargs):
    result = cls.objects.filter_by(**kwargs).first()
    if result is None:
        raise Http404
    return result