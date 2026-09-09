from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Invoice
from .forms import ClientForm, InvoiceForm, LineItemFormSet


@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(owner=request.user).select_related("client")
    return render(request, "invoices/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("client").prefetch_related("line_items"),
        pk=pk,
        owner=request.user,
    )
    return render(request, "invoices/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST, owner=request.user)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.owner = request.user
            invoice.save()
            formset = LineItemFormSet(request.POST, instance=invoice)
            if formset.is_valid():
                formset.save()
                return redirect("invoice_detail", pk=invoice.pk)
        else:
            formset = LineItemFormSet(request.POST)
    else:
        form = InvoiceForm(owner=request.user)
        formset = LineItemFormSet()
    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "formset": formset, "title": "New Invoice"},
    )


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice, owner=request.user)
        formset = LineItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice, owner=request.user)
        formset = LineItemFormSet(instance=invoice)
    return render(
        request,
        "invoices/invoice_form.html",
        {"form": form, "formset": formset, "title": f"Edit Invoice {invoice.invoice_number}", "invoice": invoice},
    )


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.owner = request.user
            client.save()
            return redirect("invoice_list")
    else:
        form = ClientForm()
    return render(request, "invoices/client_form.html", {"form": form, "title": "New Client"})