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
    list_display = ('name', 'points_cost', 'quantity_available', 'minimum_tier', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'minimum_tier')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Reward Details', {
            'fields': ('name', 'description', 'points_cost', 'quantity_available', 'minimum_tier', 'is_active')
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

    actions = [
        'approve_redemptions',
        'reject_redemptions',
        'mark_ready_for_collection',
        'mark_collected',
        'mark_completed',
    ]

    def _change_status(self, request, queryset, new_status):
        from django.db import transaction
        from notifications.services import create_notification

        updated = 0
        with transaction.atomic():
            for obj in queryset.select_for_update():
                old = obj.status
                obj.status = new_status
                obj.save(update_fields=['status'])
                updated += 1
                # generate notification for user
                title = f"Your redemption status changed to {obj.get_status_display()}"
                message = f"Your redemption of '{obj.reward.name}' is now {obj.get_status_display()}."
                try:
                    create_notification(obj.user, title, message, 'reward_redeemed')
                except Exception:
                    # don't block admin action on notification failure
                    pass
        self.message_user(request, f"Updated {updated} redemptions to {new_status}.")

    def approve_redemptions(self, request, queryset):
        return self._change_status(request, queryset, 'approved')

    def reject_redemptions(self, request, queryset):
        return self._change_status(request, queryset, 'rejected')

    def mark_ready_for_collection(self, request, queryset):
        return self._change_status(request, queryset, 'ready_for_collection')

    def mark_collected(self, request, queryset):
        return self._change_status(request, queryset, 'collected')

    def mark_completed(self, request, queryset):
        return self._change_status(request, queryset, 'completed')


admin.site.register(PointsLedger, PointsLedgerAdmin)
admin.site.register(Reward, RewardAdmin)
admin.site.register(RewardRedemption, RewardRedemptionAdmin)