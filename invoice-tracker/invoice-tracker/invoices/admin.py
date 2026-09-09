from django.contrib import admin
from .models import Client, Invoice, LineItem


class LineItemInline(admin.TabularInline):
    model = LineItem
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "owner", "created_at")
    search_fields = ("name", "email")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "client", "status", "issue_date", "due_date", "total")
    list_filter = ("status",)
    inlines = [LineItemInline]
