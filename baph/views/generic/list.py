from django.shortcuts import render
from django.views.generic import ListView as DjangoListView

#from baph.views.generic import View
from baph.views.generic.mixins import FieldsetMixin, ActionsMixin, TemplateNamesMixin


class FilteringMixin(object):

    def apply_filtering(self, query):
        """ a hook for applying filters and such """
        return query

class ListView(TemplateNamesMixin, ActionsMixin, FilteringMixin, FieldsetMixin,
               DjangoListView):
    template_name = 'models/list.html'

    def get_title(self, request):
        return self.model._meta.verbose_name_plural.capitalize()

    def get_context_data(self, **kwargs):
        context = {
            'table_title': self.get_title(self.request),
            }
        context.update(kwargs)
        return super(ListView, self).get_context_data(**context)

class GroupedListView(ListView):
    template_name = 'models/block_list.html'
    groupby = None

    def get_title(self, request):
        return 'Block List generic title'

    def get_context_data(self, **kwargs):
        context = {
            'table_title': None,
            'block_action_func': self.get_block_actions,
            'block_groupby': self.groupby,
            'block_keys': list(self.get_block_keys()),
            'block_header_formatter': self.format_block_header,
            }
        context.update(kwargs)
        return super(GroupedListView, self).get_context_data(**context)

    def get_block_actions(self, block_value):
        return []

    def get_block_keys(self):
        raise Exception('get_block_keys is not defined')

    def format_block_header(self, value):
        return value