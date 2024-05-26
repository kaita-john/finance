# urls.py

from django.urls import path

from .views import CollectionListView, CollectionDetailView, CollectionCreateView, OverpaymentCollectionListView

urlpatterns = [
    path('create', CollectionCreateView.as_view(), name="collection-create"),
    path('list', CollectionListView.as_view(), name="collection-list"),
    path('overpayments/list', OverpaymentCollectionListView.as_view(), name="collection-list"),
    path('<str:pk>', CollectionDetailView.as_view(), name="collection-detail")
]
