# urls.py

from django.urls import path

from .views import VoucherAttatchmentListView, VoucherAttatchmentDetailView, VoucherAttatchmentCreateView

urlpatterns = [
    path('create', VoucherAttatchmentCreateView.as_view(), name="VoucherAttatchment-create"),
    path('list', VoucherAttatchmentListView.as_view(), name="VoucherAttatchment-list"),
    path('<str:pk>', VoucherAttatchmentDetailView.as_view(), name="VoucherAttatchment-detail")
]
