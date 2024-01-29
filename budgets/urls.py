# urls.py

from django.urls import path

from .views import BudgetListView, BudgetDetailView, BudgetCreateView

urlpatterns = [
    path('create', BudgetCreateView.as_view(), name="budget-create"),
    path('list', BudgetListView.as_view(), name="budget-list"),
    path('<str:pk>', BudgetDetailView.as_view(), name="budget-detail")
]
