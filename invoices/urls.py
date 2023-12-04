# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('create', InvoiceCreateView.as_view(), name="invoice-create"),
    path('list', InvoiceListView.as_view(), name="invoice-list"),
    path('invoice', InvoiceStructureView.as_view(), name='invoice-structure'),
    path('invoice-classes', InvoiceClassesListView.as_view(), name='invoice-structure'),
    path('<str:pk>', InvoiceDetailView.as_view(), name="invoice-detail")
]
