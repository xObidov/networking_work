from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("charts/revenue/", views.monthly_revenue_data, name="chart_revenue"),
    path("charts/leads/", views.lead_conversion_data, name="chart_leads"),
    path("charts/growth/", views.sales_growth_data, name="chart_growth"),
    path("charts/performance/", views.employee_performance_data, name="chart_performance"),
]
