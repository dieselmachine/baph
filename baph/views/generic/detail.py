from django.shortcuts import render
from django.views.generic import DetailView as DjangoDetailView

from baph.views.generic.mixins import FieldsetMixin, ActionsMixin


class DetailView(ActionsMixin, FieldsetMixin, DjangoDetailView):
    template_name = 'models/view.html'
    pk_url_kwarg = 'id'

    def apply_filtering(self, query):
        resolver = self.request.resolver_match
        return query.filter_by(**resolver.kwargs)

    def get_title(self):
        return str(self.item)