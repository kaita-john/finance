# urls.py

from django.urls import path

from .views import PIKReceiptListView, PIKReceiptDetailView, PIKReceiptCreateView

urlpatterns = [
    path('create', PIKReceiptCreateView.as_view(), name="collection-create"),
    path('list', PIKReceiptListView.as_view(), name="collection-list"),
    path('<str:pk>', PIKReceiptDetailView.as_view(), name="collection-detail")
]
