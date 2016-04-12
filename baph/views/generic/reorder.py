import urlparse

from django.contrib import messages
from django.db import connections
from django.shortcuts import render, redirect
from django.views.generic import ListView as DjangoListView

from baph.views.generic.mixins import FieldsetMixin, ActionsMixin


class ReorderView(ActionsMixin, DjangoListView):
    template_name = 'models/reorder.html'
    reorder_field = None

    def get_title(self, request):
        return 'Reordering %s' % self.model._meta.verbose_name_plural.capitalize()

    def get_queryset(self):
        reorder_col = getattr(self.model, self.reorder_field)
        return self.model.objects \
            .order_by(reorder_col)

    def get_context_data(self, **kwargs):
        context = {
            'model': self.model,
            }
        context.update(kwargs)
        return super(ReorderView, self).get_context_data(**context)

    def post(self, request, *args, **kwargs):
        items = self.get_queryset()
        session = connections['default'].session()
        data = urlparse.parse_qsl(request.body)
        data = [str(x[1]) for x in data if x[0] == 'order']
        for item in items:
            setattr(item, self.reorder_field, data.index(str(item.id)))
            session.add(item)
        session.commit()

        if request.is_ajax():
            rsp = {
                'status': 'success',
                'message': u'Items have been reordered',
                }
            return HttpResponse(json.dumps(rsp),
                content_type="application/json")
        
        messages.success(request, u'objects have been reordered')
        view = 'index'
        return redirect('%s:%s' % (request.namespace, view))