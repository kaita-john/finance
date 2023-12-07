# urls.py

from django.urls import path

from .views import ReceiptListView, ReceiptDetailView, ReceiptCreateView

urlpatterns = [
    path('create', ReceiptCreateView.as_view(), name="collection-create"),
    path('list', ReceiptListView.as_view(), name="collection-list"),
    path('<str:pk>', ReceiptDetailView.as_view(), name="collection-detail")
]
