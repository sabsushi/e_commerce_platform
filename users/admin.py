# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = "Profile"
    fields = ['role', 'bio']


class CustomUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'email', 'get_role', 'is_staff', 'is_active']
    list_filter = ['profile__role', 'is_staff', 'is_active']
    inlines = [ProfileInline]

    def get_role(self, obj):
        try:
            return obj.profile.role
        except Exception:
            return '-'
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'role', 'bio']
    list_filter   = ['role']
    search_fields = ['user__username', 'user__email']