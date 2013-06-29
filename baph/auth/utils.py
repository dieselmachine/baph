import types

from baph.db.orm import Base


def has_perm(user, resource, action, filters={}):
    # TODO: remove this shim
    return user.has_perm(resource, action, filters)

def has_resource_perm(user, resource):
    # TODO: remove this shim
    return user.has_resource_perm(resource)

def build_filter_list(user, resource, action):
    '''
    builds a list of filters suitable for use in filter expressions
    eg: object_list.filter(or_(*filters))
    --params:
    user: user object for which to check permissions
    resource: name of the resource to check
    action: name of action to check permissions against
    '''
    perms = user.get_resource_permissions(resource, action)
    if not perms:
        return ['0=1']
    return perms_to_filters(perms)
    
def perms_to_filters(perms):
    formatted = []
    for p in perms:
        if not p.key:
            # this is a boolean permission (no filters involved)
            return []

        cls = Base._decl_class_registry[p.base_class]
        keys = p.key.split(',')
        values = p.value.split(',')
        data = zip(keys, values)

        filters = []
        for key, value in data:
            frags = key.split('.')
            #cls = Base._decl_class_registry[frags.pop(0)]
            attr = frags.pop()
            for frag in frags:
                rel = getattr(cls, frag)
                cls = rel.property.argument
                if isinstance(cls, types.FunctionType):
                    # lazy-loaded attr that hasn't been evaluated yet
                    cls = cls()
                if hasattr(cls, 'is_mapper') and cls.is_mapper:
                    # we found a mapper, grab the class from it
                    cls = cls.class_
            col = getattr(cls, attr)
            filters.append(col == value)

        if len(filters) == 1:
            formatted.append(filters[0])
        else:
            formatted.append(and_(*filters))
    return formatted
