from django.urls import path

from .views import charge_view, mpesa_payment

urlpatterns = [
    path("", charge_view, name="charge_view"),
    path("mpesa-payment/", mpesa_payment, name="mpesa_payment"),
]
