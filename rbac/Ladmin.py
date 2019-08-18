from Ladmin.service.Ladmin import site,ModelLadmin
from .models import *

class PermissionConfig(ModelLadmin):
    list_display = ["title","url","action","group"]

site.register(User,)
site.register(Permission,PermissionConfig)
site.register(PermissionGroup)
site.register(Role)