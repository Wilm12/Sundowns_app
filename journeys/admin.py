from django.contrib import admin

from .models import Journey


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ("supporter", "branch", "match", "status", "created_at")
    list_filter = ("status", "branch", "match")
    search_fields = ("supporter__username", "supporter__email", "branch__name", "match__opponent")
    ordering = ("-created_at",)
