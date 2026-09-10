from django.urls import path
from . import views

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
       path("dashboard/", views.dashboard, name="dashboard"),
    path("new/", views.invoice_create, name="invoice_create"),
    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
     path("<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("<int:pk>/delete/", views.invoice_delete, name="invoice_delete"),
]