from django.contrib import admin
from .models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'membership', 'amount', 'status', 'payment_date')
    list_filter = ('status', 'payment_date')
    search_fields = ('membership__user__username', 'membership__user__email')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date', 'id')
    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'membership', 'amount', 'status')
        }),
        ('Timestamp', {
            'fields': ('payment_date',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Payment, PaymentAdmin)