# urls.py

from django.urls import path

from .views import TransactionListView, TransactionDetailView, TransactionCreateView, SettleTransactionView

urlpatterns = [
    path('create', TransactionCreateView.as_view(), name="transaction-create"),
    path('list', TransactionListView.as_view(), name="transaction-list"),
    path('settle/<str:pk>', SettleTransactionView.as_view(), name="settle-transaction"),
    path('<str:pk>', TransactionDetailView.as_view(), name="transaction-detail")
]
