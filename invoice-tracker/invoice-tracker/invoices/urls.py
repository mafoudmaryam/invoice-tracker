from django.urls import path
from . import views

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("new/", views.invoice_create, name="invoice_create"),
    path("clients/new/", views.client_create, name="client_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
]