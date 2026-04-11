from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("landlord/properties/new/", views.add_property, name="landlord-add-property"),
    path("landlord/dashboard/", views.landlord_page, {"page": "overview"}, name="landlord-dashboard"),
    path("landlord/overview/", views.landlord_page, {"page": "overview"}, name="landlord-overview"),
    path("landlord/properties/", views.landlord_page, {"page": "properties"}, name="landlord-properties"),
    path("landlord/tenants/", views.landlord_page, {"page": "tenants"}, name="landlord-tenants"),
    path("landlord/payments/", views.landlord_page, {"page": "payments"}, name="landlord-payments"),
    path("landlord/maintenance/", views.landlord_page, {"page": "maintenance"}, name="landlord-maintenance"),
    path("landlord/analytics/", views.landlord_page, {"page": "analytics"}, name="landlord-analytics"),
    path("landlord/notifications/", views.landlord_page, {"page": "notifications"}, name="landlord-notifications"),
    path("landlord/settings/", views.landlord_page, {"page": "settings"}, name="landlord-settings"),
]
