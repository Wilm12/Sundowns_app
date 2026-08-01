from django.contrib import admin

from .models import StudentVerification, SupporterEligibility


@admin.register(SupporterEligibility)
class SupporterEligibilityAdmin(admin.ModelAdmin):
    list_display = ("supporter", "is_eligible", "reason", "evaluated_at", "expires_at")
    list_filter = ("is_eligible", "reason")
    search_fields = ("supporter__username", "supporter__email")
    ordering = ("-evaluated_at",)


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "student_number", "status", "verified_at", "expires_at")
    list_filter = ("status", "university")
    search_fields = ("user__username", "user__email", "student_number", "university")
    ordering = ("-created_at",)
