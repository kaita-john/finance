# urls.py

from django.urls import path

from .views import VoucherItemListView, VoucherItemDetailView, VoucherItemCreateView

urlpatterns = [
    path('create', VoucherItemCreateView.as_view(), name="voucher-item-create"),
    path('list', VoucherItemListView.as_view(), name="voucher-item-list"),
    path('<str:pk>', VoucherItemDetailView.as_view(), name="voucher-item-detail")
]
