from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'department', 'admission_date','shift')
    search_fields = ('name', 'position', 'department','shift')