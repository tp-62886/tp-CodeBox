from django.contrib import admin
from .models import Job


# Register your models here.

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('GZZWLBMC',)
    search_fields = list_display
    list_filter = list_display
