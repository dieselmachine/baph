import sys

from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.backends import jinja2 as jinja2backend
from django.template.context import make_context
from django.utils import six
import jinja2


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

