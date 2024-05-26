# urls.py

from django.urls import path

from .views import PaymentInKindListView, PaymentInKindDetailView, PaymentInKindCreateView, OverpaymentPaymentInKindListView

urlpatterns = [
    path('create', PaymentInKindCreateView.as_view(), name="collection-create"),
    path('list', PaymentInKindListView.as_view(), name="collection-list"),
    path('overpayments/list', OverpaymentPaymentInKindListView.as_view(), name="collection-list"),
    path('<str:pk>', PaymentInKindDetailView.as_view(), name="collection-detail")
]
