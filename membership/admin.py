from django.contrib import admin
from .models import Membership


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'status', 'start_date', 'expiry_date')
    list_filter = ('tier', 'status', 'start_date', 'expiry_date')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'start_date'
    readonly_fields = ('id',)
    fieldsets = (
        ('Membership Details', {
            'fields': ('id', 'user', 'tier', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'expiry_date')
        }),
    )
    list_per_page = 50


admin.site.register(Membership, MembershipAdmin)