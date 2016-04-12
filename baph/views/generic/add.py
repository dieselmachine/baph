from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import resolve_url
from django.views.generic import CreateView

#from baph.views.generic.base import TemplateView
from baph.views.generic.mixins import FieldsetMixin, ActionsMixin


class AddView(ActionsMixin, SuccessMessageMixin, CreateView):
    template_name = 'models/add.html'
    form_modals_template_name = None
    post_form_template_name = None
    quantity_field = None

    def alter_form_data(self, request, data):
        # hook for updating form data before applying to object
        return data

    def get_title(self):
        return 'Add a new %s' % self.model._meta.verbose_name

    def get_success_message(self, cleaned_data):
        return '%s has been added' % str(self.object)

    def get_success_url(self):
        return '../'

    '''
    def get(self, request, **kwargs):
        #custom_fields = self.get_custom_fields(request)

        form = self.form_class(extension_owner=request.client.id,
                            **self.get_form_kwargs(request))

        context = self.get_context_data(
            form=form, 
            form_modals=self.form_modals_template_name,
            post_form=self.post_form_template_name,
            )

        return render(request, self.template_name, context)
    '''
    '''
    def post(self, request, **kwargs):
        form = self.form_class(request.POST, extension_owner=request.client.id,
                            **self.get_form_kwargs(request))

        if not form.is_valid():
            messages.error(request, 'Please correct the errors below')
            context = self.get_context_data(request,
                form=form, 
                form_modals=self.form_modals_template_name,
                post_form=self.post_form_template_name,
                )
            return render(request, self.template_name, context)

        custom_fields = self.get_custom_fields(request)

        data = form.cleaned_data
        if custom_fields:
            # move extended data into the appropriate field
            data[self.extension_field] = {}
            for field in custom_fields:
                if field.slug in data:
                    data[self.extension_field][field.slug] = data.pop(field.slug)
        data = self.alter_form_data(request, data)

        args = self.get_detail_uri_args(request)

        # save to db
        session = orm.sessionmaker()
        if self.quantity_field:
            # multiple object add
            count = data.pop(self.quantity_field, 1)
            for c in range(count):
                item = self.model(**data)
                session.add(item)
            msg = '%s calls have been added' % count
        else:
            item = self.model(**data)
            session.add(item)
            msg = '%s has been added' % item
        session.commit()

        messages.success(request, msg)
        return redirect('%s:%s' % (request.namespace, self.success_view),
            *args)
    '''