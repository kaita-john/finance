# urls.py

from django.urls import path

from .views import ReceiptListView, ReceiptDetailView, ReceiptCreateView


urlpatterns = [
    path('create', ReceiptCreateView.as_view(), name="receipt-create"),
    path('list', ReceiptListView.as_view(), name="receipt-list"),
    path('<str:pk>', ReceiptDetailView.as_view(), name="receipt-detail")
]
