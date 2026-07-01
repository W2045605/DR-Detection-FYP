from django.contrib import admin
from .models import ClinicianProfile

@admin.register(ClinicianProfile)
class ClinicianProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'medical_id', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['medical_id', 'user__username', 'user__email']


