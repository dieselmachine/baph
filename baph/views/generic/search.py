from django.db.models.constants import LOOKUP_SEP
from django.forms import Form
from django.shortcuts import render
from sqlalchemy import and_, or_

from baph.forms.fields import NullCharField
from baph.views.generic import ListView
from baph.views.generic.mixins import FieldsetMixin, ActionsMixin


class SearchView(ListView):
    template_name = 'models/search.html'
    filtering = []
    search_fields = None
    
    def get_title(self, request):
        return 'Search %s' % self.model._meta.verbose_name_plural

    def get_context_data(self, **kwargs):
        #assert False
        return super(SearchView, self).get_context_data(
                     form=self.form, 
                     method='GET',
                     table_title='Results',
                     **kwargs)

    def get_search_form(self, request):
        model = self.model
        filtering = self.filtering
        search_fields = self.search_fields

        class SearchForm(Form):
            def __init__(self, *args, **kwargs):
                super(SearchForm, self).__init__(*args, **kwargs)

                if search_fields:
                    self.fields['q'] = NullCharField(label='Keywords', 
                                                     required=False)
                
                for f in filtering:
                    attr = getattr(model, f)
                    prop = attr.property
                    col = prop.columns[0]
                    opt_func = getattr(model, 'get_%s_options' % f, None)
                    if opt_func:
                        self.fields[f] = NullChoiceField(
                            required=False,
                            choices=opt_func(request))
                    elif type(col.type) == Boolean:
                        self.fields[f] = NullBooleanChoiceField(
                            required=False)
                    elif type(col.type) == Date:
                        self.fields[f+'__ge'] = forms.DateField(
                            required=False,
                            label='%s (start)' % f,
                            widget=forms.TextInput(
                                attrs={'data-date-format': 'yyyy-mm-dd'}),
                            )
                        self.fields[f+'__lt'] = forms.DateField(
                            required=False,
                            label='%s (end)' % f,
                            widget=forms.TextInput(
                                attrs={'data-date-format': 'yyyy-mm-dd'}),
                            )
                    else:
                        raise Exception('undefined data type: %s' % col.type)
        return SearchForm

    def convert_filters(self, filters):
        # converts filters in querydict format to sqla format
        and_filters = []
        for filter_expr, value in filters.items():
            if value is None:
                # ignore fields with no value provided
                continue

            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'eq'

            if field_name in self.filtering:
                # filter field
                if len(filter_bits):
                    filter_type = filter_bits.pop()
                attr = getattr(self.model, field_name)
                op = getattr(operator, filter_type)
                and_filters.append(op(attr,value))
            
            elif field_name == 'q':
                # searchable fields
                if not value:
                    # no null searches for strings
                    continue

                or_filters = []
                q = value.encode('utf8')
                for key in self.search_fields:
                    attr = getattr(self.model, key)
                    col = attr.property.columns[0]
                    col_type = col.type.python_type
                    if issubclass(col_type, basestring):
                        # any search term can be a string match
                        or_filters.append(col.like('%%%s%%' % q))
                    elif issubclass(col_type, int):
                        # only try this if the query is numeric
                        if q.isdigit():
                            or_filters.append(col.match(q))
                and_filters.append(or_(*or_filters))
        return and_filters

    def apply_filtering(self, request, query):
        form_class = self.get_search_form(request)
        if request.GET:
            # search criteria exists, process it
            self.form = form_class(data=request.GET)
            if self.form.is_valid():
                filters = self.form.cleaned_data
            else:
                filters = None
                messages.error(request, 'Please correct the errors below')
        else:
            filters = None
            self.form = form_class()

        if filters:
            filters = self.convert_filters(filters)
            query = query.filter(and_(*filters))
        return query        

    def get(self, request, *args, **kwargs):
        # load items from db
        items = self.get_queryset()
        items = self.apply_filtering(request, items)
        show_results = True
        # TODO: apply authorization filters to items
        if not request.GET:
            # only show results on a search
            show_results = False
            items = []

        context = self.get_context_data(object_list=items,
                                        show_results=show_results)

        return render(self.request, self.template_name, context)