#encoding: utf-8
from __future__ import absolute_import
import sys

from django.core.urlresolvers import reverse
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends import jinja2 as jinja2backend
from django.template.base import TemplateSyntaxError, Token
from django.template.context import _builtin_context_processors, make_context
from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
import jinja2
from jinja2.ext import Extension


class Jinja2(jinja2backend.Jinja2):
    
    app_dirname = 'templates'
    
    def from_string(self, template_code):
        return Template(self.env.from_string(template_code), self.env)

    def get_template(self, template_name):
        try:
            template = self.env.get_template(template_name)
            return Template(template, self.env)
        except jinja2.TemplateNotFound as exc:
            six.reraise(TemplateDoesNotExist, TemplateDoesNotExist(exc.args),
                        sys.exc_info()[2])
        except jinja2.TemplateSyntaxError as exc:
            six.reraise(TemplateSyntaxError, TemplateSyntaxError(exc.args),
                        sys.exc_info()[2])

class JinjaEnvironment(jinja2.Environment):
    def __init__(self, *args, **kwargs):
        self.context_processors = kwargs.pop('context_processors', [])
        super(JinjaEnvironment, self).__init__(*args, **kwargs)

    @cached_property
    def template_context_processors(self):
        context_processors = _builtin_context_processors
        context_processors += tuple(self.context_processors)
        return tuple(import_string(path) for path in context_processors)


class Template(jinja2backend.Template):
    def __init__(self, template, engine):
        super(Template, self).__init__(template)
        self.name = template.filename
        self.engine = engine

    def render(self, context=None, request=None):
        context = make_context(context, request)
        context.render_context.push()
        try:
            if context.template is None:
                with context.bind_template(self):
                    context.template_name = self.name
                    return self.template.render(context.flatten())
            else:
                return self.template.render(context.flatten())
        finally:
            context.render_context.pop()
        
class URLExtension(Extension):
    tags = set(['url'])

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        viewname = None
        args = []
        kwargs = []
        asvar = None

        # read viewname first
        if parser.stream.current.type == 'string':
            token = next(parser.stream)
            viewname = jinja2.nodes.Const(token.value, lineno=token.lineno)
        else:
            viewname = parser.parse_expression()

        while parser.stream.current.type != 'block_end':
            if parser.stream.current.type == 'name':
                if parser.stream.look().type == 'assign':
                    key = jinja2.nodes.Const(next(parser.stream).value)
                    next(parser.stream)
                    value = parser.parse_expression()
                    kwargs.append(jinja2.nodes.Pair(key, value, lineno=key.lineno))
                    continue
                if parser.stream.look().type == 'dot':
                    args.append(parser.parse_expression())
                    continue
                if parser.stream.current.value == 'as':
                    next(parser.stream)
                    asvar = jinja2.nodes.Name(parser.stream.expect('name').value,
                            'store')
                    continue
                raise Exception()
            elif parser.stream.current.type != 'string':
                expr = parser.parse_expression()
                args.append(expr)
                continue
            else:
                token = next(parser.stream)
                args.append(jinja2.nodes.Const(token.value, lineno=token.lineno))
                continue
            args.append(token.value)

        def make_call_node(*kw):
            print (kw, viewname, args, kwargs, asvar)
            return self.call_method('_reverse', args=[
                viewname,
                jinja2.nodes.List(args),
                jinja2.nodes.Dict(kwargs),
                jinja2.nodes.Name('_current_app', 'load'),
                ], kwargs=kw)

        if asvar:
            call_node = make_call_node(jinja2.nodes.Keyword('fail',
                jinja2.nodes.Const(False)))
            return jinja2.nodes.Assign(asvar, call_node)
        else:
            return jinja2.nodes.Output([make_call_node()]).set_lineno(lineno)

    @classmethod
    def _reverse(self, viewname, args, kwargs, current_app=None, fail=True):
        from django.core.urlresolvers import reverse, NoReverseMatch
        print (viewname, args, kwargs, current_app, fail)
        url = ''
        urlconf=kwargs.pop('urlconf', None)
        try:
            url = reverse(viewname, urlconf=urlconf, args=args, kwargs=kwargs,
                          current_app=current_app)
        except NoReverseMatch:
            if fail:
                raise
            return ''
        return url