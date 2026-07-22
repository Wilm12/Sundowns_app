from django.contrib import admin
from .models import Branch


class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'status', 'location', 'contact_email', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'branch_code', 'location', 'contact_email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'id')
    fieldsets = (
        ('Branch Information', {
            'fields': ('id', 'name', 'branch_code', 'location', 'status')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Branch, BranchAdmin)