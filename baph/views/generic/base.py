from django.core.urlresolvers import reverse
from django.views.generic import base

from baph.contrib.fieldset_config.models import UserViewConfig


ACTION_ICONS = {
    'activate': 'eye-open',
    'add':  'plus',
    'clone': '',
    'edit': 'pencil',
    'delete': 'bin',
    'deactivate': 'eye-close',
    'import': 'import',
    'export': 'export',
    'extend': 'list-alt',
    'publish': 'share',
    'reorder': 'sort',
    'search':   'search',
    'unpublish': 'unshare',
    'view': 'zoom_in',
    }

"""
class View(base.View):
    model = None
    required_uri_kwargs = []
    fields = None
    excludes = None
    labels = {}
    help_texts = {}
    detail_post_actions = []
    subheader_post_actions = []
    
    @property
    def extension_field(self):
        return self.model._meta.extension_field

    @property
    def extension_owner(self):
        return self.model._meta.extension_owner_field

    def get_context_data(self, **kwargs):
        '''
        extension_field = None
        if hasattr(self.model, 'get_custom_fields'):
            extension_field = self.model._meta.extension_field

        ns_args = []
        ns_kwargs = {}
        for k in self.required_uri_kwargs:
            # we will need extra params to build urls
            v = request.url.kwargs[k]
            ns_args.append(v)
            ns_kwargs[k] = v
        '''
        if 'view' not in kwargs:
            kwargs['view'] = self
        kwargs.update({
            'subheader_brand': self.get_subheader_brand(self.request),
            'subheader_action_func': self.get_subheader_actions,
            'detail_action_func': self.get_detail_actions,
            'icons': ACTION_ICONS,
            })
        '''
        context = {
            'extension': extension_field,
            'model': self.model,
            'title': self.get_title(request),
            'ns_args': ns_args,
            'ns_kwargs': ns_kwargs,
            'url_kwargs': ns_kwargs,
            }
        context.update(kwargs)
        return context
        '''
        return kwargs

    def get_custom_fields(self, request):
        custom_fields = []
        if self.model._meta.extension_field:
            custom_fields = CustomField.objects \
                               .filter_by(owner_id=request.client_id) \
                               .filter_by(model=self.model._meta.object_name) \
                               .all()
        return custom_fields        
    
    def get_detail_uri_args(self, request):
        args = []
        for k in self.required_uri_kwargs:
            # we will need extra params to build detail urls
            args.append(request.url.kwargs[k])
        return args
    
    def get_title(self, request):
        return 'BaseView title'

    '''
    def get_detail_actions(self, request, item, namespace=None):
        if not namespace:
            resolver = request.resolver_match
            namespace = resolver.namespace
        actions = []
        for label, view, args in item.actions(request.user, namespace):
            view_name = view.rsplit(':', 1)[-1]
            new_view = '%s:%s' % (namespace, view_name)
            uri_args = self.get_detail_uri_args(request)
            try:
                url = reverse(view, args=uri_args+list(args))
            except:
                url = reverse(view, args=uri_args)
            method = 'post' if view_name in self.detail_post_actions else 'get'
            actions.append((label, url, method))
        return actions
    '''
    def get_field_config(self, request, view_name=None):
        if not view_name:
            resolver = request.resolver_match
            view_name=resolver.view_name
        config = UserViewConfig.objects \
                    .filter_by(user_id=request.user.id) \
                    .filter_by(view_name=view_name) \
                    .first()
        if not config:
            # config not found, return default for this view
            config = UserViewConfig(user_id=request.user.id,
                                    view_name=view_name,
                                    fields=self.default_list_fields)
        if self.excludes:
            # strip excluded fields
            config.fields = [f for f in config.fields \
                if f[0] not in self.excludes]
        return config

    def get_all_field_info(self, request):
        # initialize with defaults from the model
        field_names = []
        labels = self.model._meta.labels.copy()
        help_texts = self.model._meta.help_texts.copy()

        # load all column-based fields from model
        for field in self.model.get_fields():
            field_names.append(field.key)

        # add virtual fields
        for field_name in self.model._meta.virtual_fields:
            field_names.append(field_name)

        # add custom fields
        custom_fields = self.get_custom_fields(request)
        for field in custom_fields:
            field_name = field.name
            field_names.append(field_name)
            labels[field_name] = field.name
            help_texts[field_name] = field.description

        # now update with values from the view
        labels.update(self.labels)
        help_texts.update(self.help_texts)

        # if we have an explicit field list, use it
        if self.fields is not None:
            field_names = self.fields

        # remove any exclusions
        if self.excludes is not None:
            field_names = [f for f in field_names if f not in self.excludes]

        return field_names, labels, help_texts

    def get_field_info(self, request):
        field_names = [f[0] for f in self.fields]
        labels = self.model._meta.labels.copy()
        help_texts = self.model._meta.help_texts.copy()

        custom_fields = self.get_custom_fields(request)
        for field in custom_fields:
            field_name = field['name']
            field_names.append(field_name)
            labels[field_name] = field['label']
            help_texts[field_name] = field['help_text']
        return (field_names, labels, help_texts)

    def get_queryset(self, request):
        raise Exception('get_queryset is not defined')
    '''
    def get_subheader_brand(self, request):
        resolver = request.resolver_match
        namespace = resolver.namespace
        args = self.get_detail_uri_args(request)
        label = self.model._meta.verbose_name_plural.capitalize()
        try:
            url = reverse('%s:index' % namespace, args=args)
            return (label, url)
        except:
            return None
    
    def get_subheader_actions(self, request):
        resolver = request.resolver_match
        namespace = resolver.namespace
        args = self.get_detail_uri_args(request)
        actions = []
        for label, view in self.model.list_actions(request.user, namespace):
            url = reverse(view, args=args)
            view_name = view.rsplit(':', 1)[-1]
            method = 'post' if view_name in self.subheader_post_actions else 'get'
            actions.append((label, url, method))
        if self.model._meta.filtering:
            url = reverse('%s:search' % namespace, args=args)
            actions.append(('Search', url, 'get'))
        return actions
    '''
    def get_pk_kwargs(self, kwargs):
        '''
        if hasattr(new_class._meta, 'pk'):
            if isinstance(new_class._meta.pk, basestring):
                new_class._meta.pk = [new_class._meta.pk]
        else:
            new_class._meta.pk = [col.key for col in \
                inspect(new_class._meta.model).primary_key]
        '''
        
        keys = [col.key for col in inspect(self.model).primary_key]
        pk_kwargs = {}
        for key in keys:
            pk_kwargs[key] = kwargs[key]
        assert False
        return pk_kwargs
"""
'''
class TemplateView(base.TemplateResponseMixin, base.ContextMixin, View):
    """
    A view that renders a template.  This view will also pass into the context
    any keyword arguments passed by the url conf.
    """
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)
'''