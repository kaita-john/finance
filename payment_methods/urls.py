# urls.py

from django.urls import path

from .views import PaymentMethodListView, PaymentMethodDetailView, PaymentMethodCreateView

urlpatterns = [
    path('create', PaymentMethodCreateView.as_view(), name="paymentMethod-create"),
    path('list', PaymentMethodListView.as_view(), name="paymentMethod-list"),
    path('<str:pk>', PaymentMethodDetailView.as_view(), name="paymentMethod-detail")
]
