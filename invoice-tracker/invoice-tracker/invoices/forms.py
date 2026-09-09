from django import forms
from django.forms import inlineformset_factory
from .models import Client, Invoice, LineItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "invoice_number", "status", "issue_date", "due_date"]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields["client"].queryset = Client.objects.filter(owner=owner)


LineItemFormSet = inlineformset_factory(
    Invoice,
    LineItem,
    fields=["description", "quantity", "rate"],
    extra=1,
    can_delete=True,
)


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email", "phone", "address"]