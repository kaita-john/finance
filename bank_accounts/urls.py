# urls.py

from django.urls import path

from .views import BankAccountListView, BankAccountDetailView, BankAccountCreateView

urlpatterns = [
    path('create', BankAccountCreateView.as_view(), name="bankaccount-create"),
    path('list', BankAccountListView.as_view(), name="bankaccount-list"),
    path('<str:pk>', BankAccountDetailView.as_view(), name="bankaccount-detail")
]
