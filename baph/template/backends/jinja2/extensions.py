from django.core.urlresolvers import reverse
from django.template.backends.utils import csrf_input
import jinja2
from jinja2.ext import Extension


class CSRFExtension(Extension):
    tags = set(['csrf_token'])

    def _csrf_input(self, request):
        return csrf_input(request)

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        
        return jinja2.nodes.Output([
            self.call_method('_csrf_input', args=[
                jinja2.nodes.Name('request', 'load'),
                ])
            ]).set_lineno(lineno)

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
                if parser.stream.look().type == 'block_end':
                    args.append(parser.parse_expression())
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