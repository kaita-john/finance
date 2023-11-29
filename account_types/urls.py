# urls.py

from django.urls import path

from .views import AccountTypeListView, AccountTypeDetailView, AccountTypeCreateView

urlpatterns = [
    path('create', AccountTypeCreateView.as_view(), name="accounttype-create"),
    path('list', AccountTypeListView.as_view(), name="accounttype-list"),
    path('<str:pk>', AccountTypeDetailView.as_view(), name="accounttype-detail")
]
