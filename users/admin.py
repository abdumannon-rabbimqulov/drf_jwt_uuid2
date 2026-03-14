from django.contrib import admin
from .models import CustomUser,CodeVerify
# Register your models here.

admin.site.register(CodeVerify)
admin.site.register(CustomUser)