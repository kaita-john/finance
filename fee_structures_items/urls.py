# urls.py

from django.urls import path

from .views import FeeStructureItemListView, FeeStructureItemDetailView, FeeStructureItemCreateView

urlpatterns = [
    path('create', FeeStructureItemCreateView.as_view(), name="feeStructureItem-create"),
    path('list', FeeStructureItemListView.as_view(), name="feeStructureItem-list"),
    path('<str:pk>', FeeStructureItemDetailView.as_view(), name="feeStructureItem-detail")
]
