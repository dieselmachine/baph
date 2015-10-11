# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response as r2r
from django.template import RequestContext
from django.template.loader import get_template, select_template

__all__ = ['render_to_string', 'render_to_response']


def render_to_response(template_name, dictionary=None, request=None,
                       mimetype=None):
    '''Render a template into a response object. Meant to be compatible with
    the function in :mod:`djangojinja2` of the same name, distributed with
    Jinja2, as opposed to the shortcut from Django. For that, see
    :func:`coffin.shortcuts.render_to_response`.
    '''
    request_context = RequestContext(request) if request else None
    return r2r(template_name, dictionary=dictionary,
               context_instance=request_context,
               mimetype=mimetype)


def render_to_string(template_or_template_name, dictionary=None, request=None):
    '''Render a template into a string. Meant to be compatible with the
    function in :mod:`djangojinja2` of the same name, distributed with Jinja2,
    as opposed to the shortcut from Django. For that, see
    :func:`coffin.shortcuts.render_to_string`.
    '''
    dictionary = dictionary or {}
    request_context = RequestContext(request) if request else None
    if isinstance(template_or_template_name, (list, tuple)):
        template = select_template(template_or_template_name)
    elif isinstance(template_or_template_name, basestring):
        template = get_template(template_or_template_name)
    else:
        # assume it's a template
        template = template_or_template_name
    if request_context:
        request_context.update(dictionary)
    else:
        request_context = dictionary
    return template.render(request_context)
