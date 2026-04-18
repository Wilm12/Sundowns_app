from django.contrib import admin
from .models import Branch


class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'id')
    fieldsets = (
        ('Branch Information', {
            'fields': ('id', 'name', 'location')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Branch, BranchAdmin)