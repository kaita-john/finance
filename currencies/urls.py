# urls.py

from django.urls import path

from .views import CurrencyListView, CurrencyDetailView, CurrencyCreateView

urlpatterns = [
    path('create', CurrencyCreateView.as_view(), name="currency-create"),
    path('list', CurrencyListView.as_view(), name="currency-list"),
    path('<str:pk>', CurrencyDetailView.as_view(), name="currency-detail")
]
