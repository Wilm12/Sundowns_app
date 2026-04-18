from django.contrib import admin
from .models import PointsLedger


class PointsLedgerAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'reason', 'status', 'created_at', 'expiry_date')
    list_filter = ('status', 'reason', 'created_at', 'expiry_date')
    search_fields = ('user__username', 'user__email', 'reason')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'id')
    fieldsets = (
        ('Points Information', {
            'fields': ('id', 'user', 'points', 'reason', 'status')
        }),
        ('Dates', {
            'fields': ('created_at', 'expiry_date')
        }),
    )
    list_per_page = 50


admin.site.register(PointsLedger, PointsLedgerAdmin)