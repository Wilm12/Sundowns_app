from django.contrib import admin
from .models import CommunicationLog


class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'status', 'sent_at')
    list_filter = ('channel', 'status', 'sent_at')
    search_fields = ('user__username', 'user__email', 'message')
    date_hierarchy = 'sent_at'
    readonly_fields = ('sent_at', 'id')
    fieldsets = (
        ('Communication Details', {
            'fields': ('id', 'user', 'message', 'channel', 'status')
        }),
        ('Timestamp', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(CommunicationLog, CommunicationLogAdmin)