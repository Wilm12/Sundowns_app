from django.contrib import admin
from .models import Match


class MatchAdmin(admin.ModelAdmin):
    list_display = ('opponent', 'date', 'location')
    list_filter = ('date', 'location')
    search_fields = ('opponent', 'location')
    date_hierarchy = 'date'
    readonly_fields = ('id',)
    fieldsets = (
        ('Match Details', {
            'fields': ('id', 'date', 'opponent', 'location')
        }),
    )
    list_per_page = 50


admin.site.register(Match, MatchAdmin)