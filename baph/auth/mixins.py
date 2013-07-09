from sqlalchemy import inspect
from sqlalchemy.orm.util import identity_key

from baph.db.models.loading import cache
from baph.db.orm import Base, ORM


orm = ORM.get()

def string_to_model(string):
    if string in Base._decl_class_registry:
        return Base._decl_class_registry[string]
    elif string.title() in Base._decl_class_registry:
        return Base._decl_class_registry[string.title()]
    else:
        # this string doesn't match a resource
        return None

class PermissionStruct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

def column_to_attr(cls, col):
    for attr_ in inspect(cls).all_orm_descriptors:
        try:
            if col in attr_.property.columns:
                return attr_
        except:
            pass    
    return None

def key_to_value(obj, key):
    frags = key.split('.')
    col_key = frags.pop()
    current_obj = obj

    while frags:
        if not current_obj:
            # we weren't able to follow the chain back, one of the 
            # fks was probably optional, and had no value
            return None
        
        attr_name = frags.pop(0)
        previous_obj = current_obj
        previous_cls = type(previous_obj)
        current_obj = getattr(previous_obj, attr_name)
        if current_obj:
            # proceed to next step of the chain
            continue

        # relation was empty, we'll grab the fk and lookup the
        # object manually
        attr = getattr(previous_cls, attr_name)
        prop = attr.property

        related_cls = prop.argument
        if isinstance(related_cls, type(lambda x:x)):
            related_cls = related_cls()
        related_col = prop.local_remote_pairs[0][0]
        attr_ = column_to_attr(previous_cls, related_col)
        related_key = attr_.key
        related_val = getattr(previous_obj, related_key)
        if related_val is None:
            # relation and key are both empty: no parent found
            return None

        session = orm.sessionmaker()
        current_obj = session.query(related_cls).get(related_val)

    value = getattr(current_obj, col_key, None)
    if value:
        return str(value)
    return None

class UserPermissionMixin(object):

    def get_user_permissions(self):
        ctx = self.get_context()
        permissions = {}
        for assoc in self.permission_assocs:
            perm = assoc.permission
            #model = string_to_model(perm.resource)
            #model_name = model.__name__ if model else perm.resource
            model_name = perm.resource
            if model_name not in permissions:
                permissions[model_name] = {}
            if perm.action not in permissions[model_name]:
                permissions[model_name][perm.action] = set()
            perm = PermissionStruct(**perm.to_dict())
            if perm.value:
                perm.value = perm.value % ctx
            permissions[model_name][perm.action].add(perm)
        return permissions

    def get_group_permissions(self):
        ctx = self.get_context()
        permissions = {}
        for user_group in self.groups:
            if user_group.key:
                ctx[user_group.key] = user_group.value
            group = user_group.group
            org_id = getattr(group, self.org_key)
            if org_id not in permissions:
                permissions[org_id] = {}
            perms = permissions[org_id]
            for assoc in group.permission_assocs:
                perm = assoc.permission
                #model = string_to_model(perm.resource)
                #model_name = model.__name__ if model else perm.resource
                model_name = perm.resource
                if model_name not in perms:
                    perms[model_name] = {}
                if perm.action not in perms[model_name]:
                    perms[model_name][perm.action] = set()
                perm = PermissionStruct(**perm.to_dict())
                if perm.value:
                    try:
                        perm.value = perm.value % ctx
                    except KeyError as e:
                        raise Exception('Key %s not found in permission '
                            'context. If this is a single-value permission, '
                            'ensure the key and value are present on the '
                            'UserGroup association object.' % str(e))
                perms[model_name][perm.action].add(perm)
        return permissions

    def get_all_permissions(self):
        permissions = self.get_group_permissions()
        user_perms = self.get_user_permissions()
        if not user_perms:
            return permissions
        if not None in permissions:
            permissions[None] = {}
        for resource, actions in user_perms.items():
            if resource not in permissions[None]:
                permissions[None][resource] = {}
            for action, perms in actions.items():
                if action not in permissions[None][resource]:
                    permissions[None][resource][action] = set()
                permissions[None][resource][action].update(perms)
        return permissions

    def get_current_permissions(self):
        if hasattr(self, '_perm_cache'):
            return self._perm_cache

        perms = {}
        for wl, wl_perms in self.get_all_permissions().items():
            for rsrc, rsrc_perms in wl_perms.items():
                if not rsrc in perms:
                    perms[rsrc] = {}
                for action, action_perms in rsrc_perms.items():
                    if not action in perms[rsrc]:
                        perms[rsrc][action] = set()
                    perms[rsrc][action].update(action_perms)
        setattr(self, '_perm_cache', perms)
        return perms

    def get_resource_permissions(self, resource, action=None):
        if not resource:
            raise Exception('resource is required for permission filtering')
        if resource in cache.resource_map:
            # all resources based on Models will be present in the appcache
            # we grab the Model and check if the perm is being routed to its
            # parent
            cls = cache.resource_map[resource]
            if cls._meta.permission_handler:
                resource = cls._meta.permission_handler
                action = action if action == 'view' else 'edit'
        else:
            # virtual resources (defined via meta.permission_classes) will not
            # have an entry in the resource_map, these permissions cannot be
            # routed to a parent, so should exist in user perms already
        perms = self.get_current_permissions()
        if resource not in perms:
            return set()
        perms = perms.get(resource, {})
        if action:
            perms = perms.get(action, {})
        return perms
    
    def has_resource_perm(self, resource):
        if not self.is_authenticated():
            return False
        perms = self.get_resource_permissions(resource)
        return bool(perms)

    def has_perm(self, resource, action, filters={}):
        ctx = self.get_context()
        perms = self.get_resource_permissions(resource, action)
        if not perms:
            return False

        cls_name = tuple(perms)[0].base_class
        cls = Base._decl_class_registry[cls_name]
        obj = cls(**filters)
        return self.has_obj_perm(resource, action, obj)


    def has_obj_perm(self, resource, action, obj):
        #print 'has_obj_perm', resource, action, obj, obj.__dict__
        #resource = obj.__class__._meta.model_name
        # TODO: auto-generate resource by checking base_mapper of polymorphics

        if type(obj)._meta.permission_handler:
            # permissions for this object are based off parent object
            parent_obj = obj.get_parent(type(obj)._meta.permission_handler)
            if not parent_obj:
                # nothing to check perms against, assume True
                return True
            parent_res = type(parent_obj).resource_name
            if action != 'view':
                action = 'edit'
            return self.has_obj_perm(parent_res, action, parent_obj)

        ctx = self.get_context()
        perms = self.get_resource_permissions(resource, action)
        if not perms:
            return False

        perm_map = {}
        for p in perms:
            if not p.key in perm_map:
                perm_map[p.key] = set()
            perm_map[p.key].add(p.value % ctx)

        if action == 'add':
            for p in type(obj)._meta.permission_parents:
                attr = getattr(type(obj), p)
                prop = attr.property
                col = prop.local_remote_pairs[0][0]
                col_attr = column_to_attr(type(obj), col)
                if not col_attr.key in perm_map:
                    perm_map[col_attr.key] = set([None])

        for k,v in perm_map.items():
            keys = k.split(',')
            key_pieces = [key_to_value(obj, key) for key in keys]
            if key_pieces == [None]:
                value = None
            else:
                value = ','.join(key_pieces)

            if action == 'add':
                # for adding items, all filters must match
                if value and str(value) not in v:
                    if v == set([None]):
                        continue
                    return False
            else:
                # for other actions, one relevant perm is enough
                if value and str(value) in v:
                    return True

        return action == 'add'
