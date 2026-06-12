from django.urls import path

from . import views

app_name = "invoices"

urlpatterns = [
    path("", views.InvoiceListView.as_view(), name="list"),
    path("add/", views.InvoiceCreateView.as_view(), name="add"),
    path("<int:pk>/", views.InvoiceDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.InvoiceUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="delete"),
    path("<int:pk>/pdf/", views.InvoicePdfView.as_view(), name="pdf"),
]
