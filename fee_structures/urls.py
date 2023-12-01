# urls.py

from django.urls import path

from .views import FeeStructureListView, FeeStructureDetailView, FeeStructureCreateView

urlpatterns = [
    path('create', FeeStructureCreateView.as_view(), name="feeStructure-create"),
    path('list', FeeStructureListView.as_view(), name="feeStructure-list"),
    path('<str:pk>', FeeStructureDetailView.as_view(), name="feeStructure-detail")
]
