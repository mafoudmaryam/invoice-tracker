import base64

from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from .models import Client, Invoice
from .forms import ClientForm, InvoiceForm, LineItemFormSet


def save_signature_from_post(invoice, request):
    """If the signature pad was used, decode the base64 PNG data and save it."""
    data_url = request.POST.get("signature_data")
    if not data_url or not data_url.startswith("data:image"):
        return
    try:
        header, encoded = data_url.split(",", 1)
        image_data = base64.b64decode(encoded)
    except (ValueError, base64.binascii.Error):
        return
    invoice.signature.save(
        f"invoice_{invoice.pk}_signature.png",
        ContentFile(image_data),
        save=True,
    )


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
def dashboard(request):
    invoices = Invoice.objects.filter(owner=request.user).select_related("client").prefetch_related("line_items")
    today = timezone.localdate()

    totals_by_status = {"draft": 0, "sent": 0, "paid": 0, "overdue": 0}
    counts_by_status = {"draft": 0, "sent": 0, "paid": 0, "overdue": 0}
    outstanding_total = 0
    overdue_invoices = []

    for invoice in invoices:
        amount = invoice.total()
        totals_by_status[invoice.status] = totals_by_status.get(invoice.status, 0) + amount
        counts_by_status[invoice.status] = counts_by_status.get(invoice.status, 0) + 1
        if invoice.status in ("sent", "overdue"):
            outstanding_total += amount
        if invoice.status != "paid" and invoice.due_date < today:
            overdue_invoices.append(invoice)

    context = {
        "totals_by_status": totals_by_status,
        "counts_by_status": counts_by_status,
        "outstanding_total": outstanding_total,
        "overdue_invoices": overdue_invoices,
        "invoice_count": invoices.count(),
    }
    return render(request, "invoices/dashboard.html", context)


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
def invoice_pdf(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("client").prefetch_related("line_items"),
        pk=pk,
        owner=request.user,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    left = 1 * inch
    y = height - 1 * inch

    p.setFont("Helvetica-Bold", 20)
    p.drawString(left, y, f"Invoice {invoice.invoice_number}")
    y -= 0.4 * inch

    p.setFont("Helvetica", 11)
    for line in [
        f"Client: {invoice.client.name}",
        f"Status: {invoice.get_status_display()}",
        f"Issue date: {invoice.issue_date.strftime('%b')} {invoice.issue_date.day}, {invoice.issue_date.year}",
        f"Due date: {invoice.due_date.strftime('%b')} {invoice.due_date.day}, {invoice.due_date.year}",
    ]:
        p.drawString(left, y, line)
        y -= 0.25 * inch

    y -= 0.2 * inch
    p.setFont("Helvetica-Bold", 13)
    p.drawString(left, y, "Line Items")
    y -= 0.3 * inch

    col_desc, col_qty, col_rate, col_sub = left, left + 3 * inch, left + 4 * inch, left + 5 * inch
    p.setFont("Helvetica-Bold", 10)
    p.drawString(col_desc, y, "Description")
    p.drawString(col_qty, y, "Qty")
    p.drawString(col_rate, y, "Rate")
    p.drawString(col_sub, y, "Subtotal")
    y -= 0.15 * inch
    p.line(left, y, left + 6 * inch, y)
    y -= 0.2 * inch

    p.setFont("Helvetica", 10)
    for item in invoice.line_items.all():
        if y < 1.5 * inch:
            p.showPage()
            y = height - 1 * inch
            p.setFont("Helvetica", 10)
        p.drawString(col_desc, y, item.description[:45])
        p.drawString(col_qty, y, f"{item.quantity:.2f}")
        p.drawString(col_rate, y, f"${item.rate:.2f}")
        p.drawString(col_sub, y, f"${item.subtotal():.2f}")
        y -= 0.22 * inch

    y -= 0.2 * inch
    p.line(left, y, left + 6 * inch, y)
    y -= 0.3 * inch

    p.setFont("Helvetica", 11)
    p.drawString(left, y, "Subtotal:")
    p.drawRightString(left + 6 * inch, y, f"${invoice.subtotal():.2f}")
    y -= 0.22 * inch

    p.drawString(left, y, f"Discount ({invoice.discount_percent}%):")
    p.drawRightString(left + 6 * inch, y, f"-${invoice.discount_value():.2f}")
    y -= 0.22 * inch

    p.drawString(left, y, "Tax:")
    p.drawRightString(left + 6 * inch, y, f"${invoice.tax_amount:.2f}")
    y -= 0.22 * inch

    p.setFont("Helvetica-Bold", 13)
    p.drawString(left, y, "Total:")
    p.drawRightString(left + 6 * inch, y, f"${invoice.total():.2f}")
    y -= 0.3 * inch

    p.setFont("Helvetica", 11)
    p.drawString(left, y, "Deposit paid:")
    p.drawRightString(left + 6 * inch, y, f"${invoice.deposit_amount:.2f}")
    y -= 0.25 * inch

    p.setFont("Helvetica-Bold", 13)
    p.drawString(left, y, "Balance due:")
    p.drawRightString(left + 6 * inch, y, f"${invoice.balance_due():.2f}")
    y -= 0.4 * inch

    if invoice.signature:
        try:
            if y < 1.8 * inch:
                p.showPage()
                y = height - 1 * inch
            p.setFont("Helvetica", 10)
            p.drawString(left, y, "Signature:")
            y -= 0.15 * inch
            invoice.signature.open("rb")
            sig_image = ImageReader(invoice.signature)
            p.drawImage(sig_image, left, y - 1 * inch, width=2.5 * inch, height=1 * inch, mask="auto")
            invoice.signature.close()
        except Exception:
            pass

    p.showPage()
    p.save()
    return response


@login_required
def invoice_create(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST, request.FILES, owner=request.user)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.owner = request.user
            invoice.save()
            formset = LineItemFormSet(request.POST, instance=invoice)
            if formset.is_valid():
                formset.save()
                save_signature_from_post(invoice, request)
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
        form = InvoiceForm(request.POST, request.FILES, instance=invoice, owner=request.user)
        formset = LineItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            save_signature_from_post(invoice, request)
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