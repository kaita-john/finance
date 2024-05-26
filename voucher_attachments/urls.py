# urls.py

from django.urls import path

from .views import VoucherAttachmentListView, VoucherAttachmentDetailView, VoucherAttachmentCreateView

urlpatterns = [
    path('create', VoucherAttachmentCreateView.as_view(), name="VoucherAttachment-create"),
    path('list', VoucherAttachmentListView.as_view(), name="VoucherAttachment-list"),
    path('<str:pk>', VoucherAttachmentDetailView.as_view(), name="VoucherAttachment-detail")
]
