from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.CustomerListView.as_view(), name="list"),
    path("add/", views.CustomerCreateView.as_view(), name="add"),
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="delete"),
    path("<int:pk>/documents/", views.CustomerDocumentUploadView.as_view(), name="upload_document"),
]
