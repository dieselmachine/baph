from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from baph.views.generic.detail import DetailView


class ToggleView(DetailView):
    # shortcut view for changing a boolean value then redirecting to list view
    model = None
    field = None
    value = None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ToggleView, self).dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        raise Exception('GET not allowed here')
    
    @csrf_exempt
    def post(self, request, **kwargs):
        queryset = self.get_queryset(request)
        queryset = self.apply_filtering(request, queryset) # limit by pk
        self.item = queryset.first()
        if not self.item:
            # TODO: raise 404
            assert False

        current_val = getattr(self.item, self.field)
        if current_val == self.value:
            raise Exception('That value is already set')
        setattr(self.item, self.field, self.value)
        
        session = orm.sessionmaker()
        session.add(self.item)
        session.commit()

        resolver = request.resolver_match
        view_name = '%s:index' % resolver.namespace

        messages.success(request, u'action completed successfully')
        if request.is_ajax():
            rsp = {
                'redirect': reverse(view_name),
                }
            return HttpResponse(json.dumps(rsp),
                                content_type="application/json")
        return redirect(view_name)