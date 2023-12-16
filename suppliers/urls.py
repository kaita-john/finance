# urls.py

from django.urls import path

from .views import SupplierListView, SupplierDetailView, SupplierCreateView

urlpatterns = [
    path('create', SupplierCreateView.as_view(), name="supplier-create"),
    path('list', SupplierListView.as_view(), name="supplier-list"),
    path('<str:pk>', SupplierDetailView.as_view(), name="supplier-detail")
]
