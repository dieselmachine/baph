import datetime
import pytz

from baph.views.generic.mixins import ActionsMixin, FieldsetMixin
from django.http import Http404
from django.views.generic import MonthArchiveView


class DateListView(ActionsMixin, FieldsetMixin, MonthArchiveView):
    template_name = 'models/archive_month.html'
    date_field = 'start_date'
    allow_empty = True
    allow_future = True
    month_format = '%m'

    def get_year(self):
        try:
            return super(DateListView, self).get_year()
        except Http404:
            return str(datetime.datetime.now().year)

    def get_month(self):
        try:
            return super(DateListView, self).get_month()
        except Http404:
            return str(datetime.datetime.now().month)

    def get_title(self, request):
        return 'Date List generic title'