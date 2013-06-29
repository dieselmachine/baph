from sqlalchemy import inspect
from sqlalchemy.orm.util import identity_key

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
                    perm.value = perm.value % ctx
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
        if resource and not action:
            assert False
        if not resource:
            raise Exception('resource is required for permission filtering')
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
            frags = k.split('.')
            col_name = frags.pop()
            current_obj = obj
            while frags:
                attr_name = frags.pop(0)
                previous_obj = current_obj
                if not previous_obj:
                    break
                current_obj = getattr(previous_obj, attr_name)
                if current_obj is None:
                    # relation was empty, let's try manually grabbing via pk
                    attr = getattr(type(previous_obj), attr_name)
                    prop = attr.property
                    rel_cls = prop.argument
                    if isinstance(rel_cls, type(lambda x: x)):
                        rel_cls = rel_cls()
                    rel_col = prop.local_remote_pairs[0][0]
                    rel_key = rel_col.key
                    # we need to find the attr which refers to this column
                    # TODO: is there a better way?
                    for attr_ in inspect(type(previous_obj)).all_orm_descriptors:
                        try:
                            if rel_col in attr_.property.columns:
                                rel_key = attr_.key
                                break
                        except:
                            pass
                    rel_val = getattr(previous_obj, rel_key, None)
                    if rel_val is None:
                        # relation and key are both empty: no parent found
                        continue
                    else:
                        session = orm.sessionmaker()
                        current_obj = session.query(rel_cls).get(rel_val)

            if not current_obj:
                continue

            # now grab final value
            if not hasattr(current_obj, col_name):
                continue

            value = getattr(current_obj, col_name)
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
