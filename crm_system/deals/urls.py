from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.DealKanbanView.as_view(), name="kanban"),
    path("list/", views.DealListView.as_view(), name="list"),
    path("add/", views.DealCreateView.as_view(), name="add"),
    path("<int:pk>/", views.DealDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.DealUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.DealDeleteView.as_view(), name="delete"),
    path("<int:pk>/stage/", views.update_stage, name="update_stage"),
]
