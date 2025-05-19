from django.contrib import admin
from .models import User, FaceEncoding, Group, UserGroup, Device, AccessLog, AccessControl

# Register your models here.
admin.site.register(User)
admin.site.register(FaceEncoding)
admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Device)
admin.site.register(AccessLog)
admin.site.register(AccessControl)
