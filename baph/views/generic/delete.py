#from baph.views.generic import View
from django.views.generic import TemplateView


class DeleteView(TemplateView):
    template_name = 'models/delete.html'

    def apply_filtering(self, request, query):
        resolver = request.resolver_match
        return query.filter_by(**resolver.kwargs)

    def get_title(self, request):
        return 'Confirm delete'

    def get(self, request, **kwargs):
        resolver = request.resolver_match
        queryset = self.get_queryset(request)
        queryset = self.apply_filtering(request, queryset) # limit by pk
        item = queryset.first()
        if not item:
            # TODO: raise 404
            assert False

        cancel_url = reverse('%s:index' % resolver.namespace)

        context = self.get_context_data(request, name=str(item),
            cancel_url=cancel_url)

        return render_to_response(self.template_name, context,
            context_instance=RequestContext(request))


    def post(self, request, **kwargs):
        resolver = request.resolver_match
        queryset = self.get_queryset(request)
        queryset = self.apply_filtering(request, queryset) # limit by pk
        item = queryset.first()
        if not item:
            # TODO: raise 404
            assert False

        msg = '%s has been deleted' % item
        session = orm.sessionmaker()
        session.delete(item)
        session.commit()
        messages.success(request, msg)
        return redirect('%s:index' % resolver.namespace)