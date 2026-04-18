from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'branch', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at', 'branch')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    date_hierarchy = 'created_at'
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'branch', 'created_at')}),
    )
    readonly_fields = ('created_at',)
    list_per_page = 50


admin.site.register(User, UserAdmin)