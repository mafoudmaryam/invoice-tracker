from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Invoice
from .forms import ClientForm, InvoiceForm, LineItemFormSet


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("invoice_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


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
                messages.success(request, f"Invoice {invoice.invoice_number} was created.")
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
            messages.success(request, f"Invoice {invoice.invoice_number} was updated.")
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
            messages.success(request, f"Client '{client.name}' was added.")
            next_url = request.GET.get("next")
            if next_url == "invoice_create":
                return redirect("invoice_create")
            return redirect("client_list")
    else:
        form = ClientForm()
    return render(request, "invoices/client_form.html", {"form": form, "title": "New Client"})


@login_required
def client_list(request):
    clients = Client.objects.filter(owner=request.user)
    return render(request, "invoices/client_list.html", {"clients": clients})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client.name}' was updated.")
            return redirect("client_list")
    else:
        form = ClientForm(instance=client)
    return render(
        request,
        "invoices/client_form.html",
        {"form": form, "title": f"Edit {client.name}", "client": client},
    )


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, owner=request.user)
    if request.method == "POST":
        number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f"Invoice {number} was deleted.")
        return redirect("invoice_list")
    return render(request, "invoices/invoice_confirm_delete.html", {"invoice": invoice})