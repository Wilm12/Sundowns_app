from django.contrib import admin
from .models import PointsLedger, Reward, RewardRedemption


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


class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_cost', 'quantity_available', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Reward Details', {
            'fields': ('name', 'description', 'points_cost', 'quantity_available', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'points_spent', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'reward')
    search_fields = ('user__username', 'user__email', 'reward__name')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Redemption Details', {
            'fields': ('user', 'reward', 'points_spent', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


admin.site.register(PointsLedger, PointsLedgerAdmin)
admin.site.register(Reward, RewardAdmin)
admin.site.register(RewardRedemption, RewardRedemptionAdmin)