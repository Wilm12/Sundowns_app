from django.contrib import admin
from .models import Ticket


class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'match', 'status', 'created_at', 'qr_code')
    list_filter = ('status', 'created_at', 'match')
    search_fields = ('user__username', 'user__email', 'match__opponent', 'qr_code')
    date_hierarchy = 'created_at'
    readonly_fields = ('qr_code', 'created_at', 'id')
    fieldsets = (
        ('Ticket Information', {
            'fields': ('id', 'user', 'match', 'status')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Ticket, TicketAdmin)