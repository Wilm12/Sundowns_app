from django.contrib import admin

from .models import StudentVerification


@admin.register(StudentVerification)
class StudentVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "university", "student_number", "status", "verified_at", "expires_at")
    list_filter = ("status", "university")
    search_fields = ("user__username", "user__email", "student_number", "university")
    ordering = ("-created_at",)
