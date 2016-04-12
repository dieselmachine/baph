from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.views.generic import UpdateView

from baph.views.generic.mixins import FieldsetMixin, ActionsMixin


class EditView(ActionsMixin, SuccessMessageMixin, UpdateView):
    template_name = 'models/add.html'
    form_modals_template_name = None
    post_form_template_name = None
    quantity_field = None
    success_view = 'index'
    pk_url_kwarg = 'id'

    def apply_filtering(self, request, query):
        resolver = request.resolver_match
        return query.filter_by(**resolver.kwargs)

    def alter_form_data(self, request, data):
        # hook for updating form data before applying to object
        return data

    def get_title(self, request):
        return 'Editing "%s"' % self.item
    
    def get_success_message(self, cleaned_data):
        return '%s has been updated' % str(self.object)

    def get_success_url(self):
        return '../'

    #def get_form_kwargs(self):
    #    assert False

    '''
    def get_form_kwargs(self, request):
        form_kwargs = {}

        if self.extension_field:
            form_kwargs['initial'] = getattr(self.item, self.extension_field, {})
        return form_kwargs
    '''
    '''
    def get(self, request, **kwargs):
        queryset = self.get_queryset(request)
        queryset = self.apply_filtering(request, queryset) # limit by pk
        self.item = queryset.first()
        if not self.item:
            # TODO: raise 404
            assert False

        custom_fields = self.get_custom_fields(request)

        form = self.form_class(instance=self.item,
                               **self.get_form_kwargs())

        context = self.get_context_data(
            item=self.item,
            form=form, 
            form_modals=self.form_modals_template_name,
            post_form=self.post_form_template_name,
            )
        return render(self.request, self.template_name, context)
    '''
    """
    def post(self, request, **kwargs):
        resolver = request.resolver_match
        queryset = self.get_queryset(request)
        queryset = self.apply_filtering(request, queryset) # limit by pk
        self.item = queryset.first()
        if not self.item:
            # TODO: raise 404
            assert False
        
        form = self.form_class(**self.get_form_kwargs())
        if not form.is_valid():
            messages.error(request, 'Please correct the errors below')
            context = self.get_context_data(request,
                item=self.item,
                form=form, 
                form_modals=self.form_modals_template_name,
                post_form=self.post_form_template_name,
                )
            return render_to_response(self.template_name, context,
                context_instance=RequestContext(request))

        custom_fields = self.get_custom_fields(request)

        data = form.cleaned_data
        if custom_fields:
            # move extended data into the appropriate field
            if getattr(self.item, self.extension_field):
                data[self.extension_field] = \
                    getattr(self.item, self.extension_field).copy()
            else:
                data[self.extension_field] = {}
            for field in custom_fields:
                if field.slug in data:
                    data[self.extension_field][field.slug] = data.pop(field.slug)
        data = self.alter_form_data(request, data)

        # save to db
        '''
        session = orm.sessionmaker()
        self.item.update(data)
        self.item.kill_cache()
        session.add(self.item)
        session.commit()
        '''
        '''
        msg = '%s has been updated' % self.item
        messages.success(request, msg)
        '''
        args = self.get_detail_uri_args(request)
        
        return redirect('%s:%s' % (request.namespace, self.success_view),
            *args)
    """