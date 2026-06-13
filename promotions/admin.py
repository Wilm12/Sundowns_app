from django.contrib import admin
from .models import Promotion, PromotionRedemption


class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'multiplier', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'event_type', 'start_date')
    search_fields = ('name', 'title', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Promotion Details', {
            'fields': ('id', 'name', 'title', 'description')
        }),
        ('Rules', {
            'fields': ('event_type', 'multiplier', 'is_active')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


class PromotionRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'promotion', 'status', 'redeemed_at')
    list_filter = ('status', 'redeemed_at', 'promotion')
    search_fields = ('user__username', 'user__email', 'promotion__name', 'promotion__title')
    date_hierarchy = 'redeemed_at'
    readonly_fields = ('redeemed_at', 'id')
    fieldsets = (
        ('Redemption Details', {
            'fields': ('id', 'user', 'promotion', 'status')
        }),
        ('Timestamp', {
            'fields': ('redeemed_at',),
            'classes': ('collapse',)
        }),
    )
    list_per_page = 50


admin.site.register(Promotion, PromotionAdmin)
admin.site.register(PromotionRedemption, PromotionRedemptionAdmin)