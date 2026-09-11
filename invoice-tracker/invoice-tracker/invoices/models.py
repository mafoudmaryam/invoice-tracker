from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    issue_date = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    attachment = models.FileField(upload_to="invoice_attachments/", blank=True, null=True)
    signature = models.ImageField(upload_to="invoice_signatures/", blank=True, null=True)

    def subtotal(self):
        return sum(item.subtotal() for item in self.line_items.all())

    def discount_value(self):
        return self.subtotal() * (self.discount_percent / 100)

    def total(self):
        return self.subtotal() - self.discount_value() + self.tax_amount

    def balance_due(self):
        return self.total() - self.deposit_amount

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.name}"

class LineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.rate

    def __str__(self):
        return self.description
