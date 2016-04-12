from django.core.urlresolvers import resolve
from django.shortcuts import render
from django.views.generic import TemplateView

from baph.views.generic.mixins import ActionsMixin, FieldsetMixin


class ColumnsView(ActionsMixin, FieldsetMixin, TemplateView):
    template_name='models/columns.html'
    
    def get_parent_view(self, request):
        # go up one level in the path to determine the 'parent' view
        path, tmp = request.path.rsplit('columns/', 1)
        url = resolve(path)
        return url.view_name
    
    def get(self, request, **kwargs):
        # load the user's column display configuration
        view_name = self.get_parent_view(request)
        field_config = self.get_field_config(request, view_name)
        fields = field_config.fields

        # load field info
        field_names, labels, help_texts = self.get_all_field_info(request)

        # add currently hidden fields
        field_config_dict = dict(fields)
        for field_name in field_names:
            if not field_name in field_config_dict:
                # add non-visible columns
                fields.append( (field_name, 'none') )

        context = self.get_context_data(field_config=fields,
            labels=labels, help_texts=help_texts)

        return render(request, self.template_name, context)
    
    def post(self, request, **kwargs):
        resolver = request.resolver_match

        # load the user's column display configuration
        view_name = self.get_parent_view(request)
        field_config = self.get_field_config(request, view_name)

        # load field info
        field_names, labels, help_texts = self.get_all_field_info(request)

        # store the new view configuration
        data = urlparse.parse_qsl(request.body)
        data = [x for x in data if x[0] in field_names and x[1] != "none"]
        field_config.fields = data

        session = orm.sessionmaker()
        session.add(field_config)
        session.commit()

        messages.success(request, u'View configuration has been saved')
        if request.is_ajax():
            rsp = {
                'redirect': reverse(view_name, kwargs=resolver.kwargs),
                }
            return HttpResponse(json.dumps(rsp),
                                content_type="application/json")
        return redirect(view_name)