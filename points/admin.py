"""Admin configuration for points app."""

from django.contrib import admin
from .models import PointsAccount, PointsTransaction


class PointsTransactionInline(admin.TabularInline):
    """Inline display of transactions within PointsAccount admin."""
    model = PointsTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'points', 'description', 'reference_id', 'created_at')
    can_delete = False
    fields = ('transaction_type', 'points', 'description', 'reference_id', 'created_at')


@admin.register(PointsAccount)
class PointsAccountAdmin(admin.ModelAdmin):
    """Admin interface for PointsAccount model."""

    list_display = ('user', 'balance_display', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'created_at', 'updated_at', 'balance_display')
    date_hierarchy = 'created_at'
    inlines = [PointsTransactionInline]

    fieldsets = (
        ('Account Information', {
            'fields': ('id', 'user', 'balance_display')
        }),
        ('Balance', {
            'fields': ()
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def balance_display(self, obj):
        """Display the balance derived from transactions."""
        return f"{obj.balance} points"

    balance_display.short_description = "Balance (from transactions)"

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of points accounts."""
        return False

    def has_add_permission(self, request):
        """Prevent manual creation of points accounts."""
        return False


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    """Admin interface for PointsTransaction model."""

    list_display = ('user', 'transaction_type', 'points', 'description', 'reference_id', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'account__user')
    search_fields = ('account__user__username', 'account__user__email', 'description', 'reference_id')
    readonly_fields = ('account', 'transaction_type', 'points', 'description', 'reference_id', 'created_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'transaction_type')
        }),
        ('Points', {
            'fields': ('points', 'description')
        }),
        ('Reference', {
            'fields': ('reference_id',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def user(self, obj):
        """Display the username for easier identification."""
        return obj.account.user.username

    user.short_description = "User"

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of transaction records."""
        return False

    def has_add_permission(self, request):
        """Prevent manual creation of transactions via admin."""
        return False
