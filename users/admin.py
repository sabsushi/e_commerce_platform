# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


class CustomUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'email', 'is_staff']

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'role']
    list_filter   = ['role']
    search_fields = ['user__username', 'user__email']