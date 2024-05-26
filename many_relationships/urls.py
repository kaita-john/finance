# urls.py

from django.urls import path

from many_relationships.views import VehicleListView, VehicleDetailView, VehicleCreateView

urlpatterns = [
    path('create', VehicleCreateView.as_view(), name="feeStructure-create"),
    path('list', VehicleListView.as_view(), name="feeStructure-list"),
    path('<str:pk>', VehicleDetailView.as_view(), name="feeStructure-detail")
]
