# urls.py

from django.urls import path

from .views import VoucherListView, VoucherDetailView, VoucherCreateView

urlpatterns = [
    path('create', VoucherCreateView.as_view(), name="voucher-create"),
    path('list', VoucherListView.as_view(), name="voucher-list"),
    path('<str:pk>', VoucherDetailView.as_view(), name="voucher-detail")
]
