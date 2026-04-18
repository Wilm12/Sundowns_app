from django.contrib import admin
from .models import Transport, TransportBooking, TransportSettlement


class TransportAdmin(admin.ModelAdmin):
    list_display = ('id', 'branch', 'owner_id', 'capacity', 'status')
    list_filter = ('status', 'branch')
    search_fields = ('branch__name', 'owner_id')
    readonly_fields = ('id',)
    fieldsets = (
        ('Transport Details', {
            'fields': ('id', 'branch', 'owner_id', 'capacity', 'status')
        }),
    )
    list_per_page = 50


class TransportBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'transport', 'status', 'verified_at')
    list_filter = ('status', 'verified_at', 'transport')
    search_fields = ('ticket__id', 'transport__id')
    date_hierarchy = 'verified_at'
    readonly_fields = ('id',)
    fieldsets = (
        ('Booking Details', {
            'fields': ('id', 'ticket', 'transport', 'status')
        }),
        ('Verification', {
            'fields': ('verified_at',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


class TransportSettlementAdmin(admin.ModelAdmin):
    list_display = ('id', 'transport', 'owner_id', 'amount', 'status', 'payment_date')
    list_filter = ('status', 'payment_date', 'transport')
    search_fields = ('transport__id', 'owner_id')
    date_hierarchy = 'payment_date'
    readonly_fields = ('id',)
    fieldsets = (
        ('Settlement Details', {
            'fields': ('id', 'transport', 'owner_id', 'amount', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_date',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Transport, TransportAdmin)
admin.site.register(TransportBooking, TransportBookingAdmin)
admin.site.register(TransportSettlement, TransportSettlementAdmin)