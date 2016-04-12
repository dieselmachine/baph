from new import instancemethod
from threading import local

from baph.contrib.auth.models import Organization


_thread_locals = local()
org_key = Organization.get_relation_key()

def _set_current_organization(func):
    setattr(_thread_locals, org_key, instancemethod(func, 
        _thread_locals, type(_thread_locals)))

def set_current_organization(org=None):
    _set_current_client(lambda self: org)

def get_current_organization():
    current_org = getattr(_thread_locals, org_key, None)
    return current_org() if current_org else current_org

class LocalOrganizationMiddleware(object):
    def process_request(self, request):
        _set_current_organization(lambda self: getattr(request, org_key, None))

