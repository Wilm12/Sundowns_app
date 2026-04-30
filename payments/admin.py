from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'membership',
        'amount',
        'status',
        'reference',
        'paid_at',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
        'paid_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'membership__user__username',
        'membership__user__email',
        'reference',
    )

    readonly_fields = (
        'created_at',
    )

    date_hierarchy = 'created_at'
