from django.contrib import admin
from .models import Promotion, PromotionRedemption


class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_tier', 'status', 'expiry_date')
    list_filter = ('status', 'target_tier', 'expiry_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'expiry_date'
    readonly_fields = ('id',)
    fieldsets = (
        ('Promotion Details', {
            'fields': ('id', 'title', 'description', 'target_tier')
        }),
        ('Status & Dates', {
            'fields': ('status', 'expiry_date')
        }),
    )
    list_per_page = 50


class PromotionRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'promotion', 'status', 'redeemed_at')
    list_filter = ('status', 'redeemed_at', 'promotion')
    search_fields = ('user__username', 'user__email', 'promotion__title')
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