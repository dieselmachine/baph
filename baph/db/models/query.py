from django.db import connections
from django.db.models.constants import LOOKUP_SEP
from sqlalchemy import inspect, and_, distinct, func
from sqlalchemy.orm import query


ops = {
    'like':         'like',
    'ilike':        'ilike',
    'exact':        '__eq__',
    'iexact':       'ilike',
    'contains':     'contains',
    'icontains':    'ilike',
    'gt':           '__gt__',
    'gte':          '__ge__',
    'lt':           '__lt__',
    'lte':          '__le__',
    'startswith':   'startswith',
    'istartswith':  'ilike',
    'endswith':     'endswith',
    'iendswith':    'ilike',
    }
filter_formats = {
    'icontains':    '%{}%',
    'istartswith':  '{}%',
    'iendswith':    '%{}',
    }

def django_filters_to_sqla_filters(cls, **filters):
    and_filters = []
    for filter_expr, value in filters.items():
        filter_bits = filter_expr.split(LOOKUP_SEP)
        field_name = filter_bits.pop(0)
        if field_name == 'pk' and not hasattr(cls, 'pk'):
            # django assumes the pk is always called 'pk', fix that here
            mapper = inspect(cls)
            field_name = mapper.primary_key[0].key
        col = getattr(cls, field_name)
        filter_type = 'exact'

        if len(filter_bits):
            filter_type = filter_bits.pop()
            if filter_type not in ops:
                raise Exception('Invalid filter type: %s' % filter_type)
        op = ops[filter_type]

        if filter_type in filter_formats:
            # case insensitive
            value = filter_formats[filter_type].format(value)
        and_filters.append(getattr(col, op)(value))
    return and_filters

class Query(query.Query):

    def __init__(self, entities, session=None, query=None, using=None, 
                 hints=None):
        if hints:
            print 'ignoring hints:', hints
        if query:
            print 'ignoring query:', query

        if using:
            session = connections[alias].session()
        return super(Query, self).__init__(entities, session)

    #def __len__(self):
    #    assert False
    #    return self.count()

    def iterator(self):
        return self

    def complex_filter(self, filter_obj):
        if isinstance(filter_obj, dict):
            return self.filter_by(**filter_obj)
        else:
            # not sure what else to expect here
            assert False

    def dates(self, field_name, kind, order='ASC'):
        """
        Returns a list of date objects representing all available dates for
        the given field_name, scoped to 'kind'.
        """
        assert kind in ("year", "month", "day"), \
            "'kind' must be one of 'year', 'month' or 'day'."
        assert order in ('ASC', 'DESC'), \
            "'order' must be either 'ASC' or 'DESC'."
        col = getattr(self.model, field_name)
        trunc = func.date_trunc(kind, col)
        query = self.from_self(trunc) \
            .distinct(trunc)
        if order == 'DESC':
            query = query.order_by(trunc.desc())
        else:
            query = query.order_by(trunc)
        return query.all()

    @property
    def model(self):
        # is this the best possible way to get this?
        return self._primary_entity.mapper.class_

    def using(self, alias):
        self.session = connections[alias or 'default'].session()
        return self

    def get(self, *args, **kwargs):
        if args and kwargs:
            # not sure when this would happen
            assert False
        if kwargs:
            # this is a django-style .get
            filters = django_filters_to_sqla_filters(self.model, **kwargs)
            return super(Query, self).filter(*filters).one()
        elif args:
            # this is a normal SQLA .get
            return super(Query, self).get(args[0])
        else:
            # this is django calling .get(), expecting one item
            num = self.count()
            if num == 1:
                return self.one()
            if not num:
                raise self.model.DoesNotExist(
                    "%s matching query does not exist." %
                    self.model._meta.object_name
                )
            raise self.model.MultipleObjectsReturned(
                "get() returned more than one %s -- it returned %s!" %
                (self.model._meta.object_name, num)
            )

    def filter(self, *args, **kwargs):
        if args and kwargs:
            # not sure when this would happen
            assert False
        if kwargs:
            # this is a django-style .filter
            filters = django_filters_to_sqla_filters(self.model, **kwargs)
            return super(Query, self).filter(*filters)
        else:
            # this is a normal SQLA .filter
            return super(Query, self).filter(*args)