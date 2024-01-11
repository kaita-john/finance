# urls.py

from django.urls import path

from .views import GrantItemListView, GrantItemDetailView, GrantItemCreateView

urlpatterns = [
    path('create', GrantItemCreateView.as_view(), name="grant-item-create"),
    path('list', GrantItemListView.as_view(), name="grant-item-list"),
    path('<str:pk>', GrantItemDetailView.as_view(), name="grant-item-detail")
]
