from django.core.urlresolvers import reverse

from baph.contrib.custom_fields.models import CustomField
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

class ActionsMixin(object):
    disable_actions = False
    detail_post_actions = []
    required_uri_kwargs = []
    subheader_post_actions = []

    def get_detail_uri_args(self):
        args = []
        for k in self.required_uri_kwargs:
            # we will need extra params to build detail urls
            args.append(self.request.url.kwargs[k])
        return args

    def get_subheader_brand(self):
        resolver = self.request.resolver_match
        namespace = resolver.namespace
        args = self.get_detail_uri_args()
        label = self.model._meta.verbose_name_plural.capitalize()
        try:
            url = reverse('%s:index' % namespace, args=args)
            return (label, url)
        except:
            return None

    def get_subheader_actions(self):
        resolver = self.request.resolver_match
        namespace = resolver.namespace
        args = self.get_detail_uri_args()
        actions = []
        for label, view in self.model.list_actions(self.request.user, namespace):
            url = reverse(view, args=args)
            view_name = view.rsplit(':', 1)[-1]
            method = 'post' if view_name in self.subheader_post_actions else 'get'
            actions.append((label, url, method))
        if self.model._meta.filtering:
            url = reverse('%s:search' % namespace, args=args)
            actions.append(('Search', url, 'get'))
        return actions

    def get_detail_actions(self, item, namespace=None):
        print 'get_detail_actions:', item, namespace
        if not namespace:
            resolver = self.request.resolver_match
            namespace = resolver.namespace
        actions = []
        for label, view, args in item.actions(self.request.user, namespace):
            print '  ', label, view, args
            view_name = view.rsplit(':', 1)[-1]
            new_view = '%s:%s' % (namespace, view_name)
            uri_args = self.get_detail_uri_args()
            try:
                url = reverse(view, args=uri_args+list(args))
            except:
                url = reverse(view, args=uri_args)
            method = 'post' if view_name in self.detail_post_actions else 'get'
            actions.append((label, url, method))
        return actions

    def get_context_data(self, **kwargs):
        kwargs.update({
            'disable_actions': self.disable_actions,
            'subheader_brand': self.get_subheader_brand(),
            'subheader_action_func': self.get_subheader_actions,
            'detail_action_func': self.get_detail_actions,
            'icons': ACTION_ICONS,
            })
        return super(ActionsMixin, self).get_context_data(**kwargs)

class FieldsetMixin(object):
    fields = None
    excludes = None
    labels = {}
    help_texts = {}

    def get_custom_fields(self, request):
        custom_fields = []
        if self.model._meta.extension_field:
            custom_fields = CustomField.objects \
                               .filter_by(owner_id=request.client_id) \
                               .filter_by(model=self.model._meta.object_name) \
                               .all()
        return custom_fields        

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

    def get_context_data(self, **kwargs):
        # load field info for all available fields
        field_names, labels, help_texts = self.get_all_field_info(self.request)

        # load the user's column display configuration
        field_config = self.get_field_config(self.request)

        kwargs.update({
            'field_config': field_config.fields,
            'fields': field_names,
            'labels': labels,
            'help_texts': help_texts,
            })
        return super(FieldsetMixin, self).get_context_data(**kwargs)

class TemplateNamesMixin(object):

    def get_template_names(self):
        """
        Returns a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        names = super(TemplateNamesMixin, self).get_template_names()
        names.append('generic/object%s' % self.template_name_suffix)
        #assert False
        return names
