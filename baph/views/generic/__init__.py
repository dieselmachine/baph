#from baph.views.generic.base import View
from baph.views.generic.add import AddView
from baph.views.generic.columns import ColumnsView
from baph.views.generic.dates import DateListView
from baph.views.generic.delete import DeleteView
from baph.views.generic.detail import DetailView
from baph.views.generic.edit import EditView
from baph.views.generic.list import ListView, GroupedListView
from baph.views.generic.reorder import ReorderView
from baph.views.generic.search import SearchView
from baph.views.generic.toggle import ToggleView


__all__ = ['AddView', 'ColumnsView', 'DateListView', 'DeleteView',
           'DetailView', 'DetailView', 'EditView', 'ListView',
           'GroupedListView', 'ReorderView', 'SearchView', 'ToggleView']