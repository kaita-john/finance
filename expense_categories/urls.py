# urls.py

from django.urls import path

from .views import ExpenseCategoryListView, ExpenseCategoryDetailView, ExpenseCategoryCreateView

urlpatterns = [
    path('create', ExpenseCategoryCreateView.as_view(), name="expense-category-create"),
    path('list', ExpenseCategoryListView.as_view(), name="expense-category-list"),
    path('<str:pk>', ExpenseCategoryDetailView.as_view(), name="expense-category-detail")
]
