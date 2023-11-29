# urls.py

from django.urls import path

from .views import FinancialYearListView, FinancialYearDetailView, FinancialYearCreateView

urlpatterns = [
    path('create', FinancialYearCreateView.as_view(), name="financial-year-create"),
    path('list', FinancialYearListView.as_view(), name="financial-year-list"),
    path('<str:pk>', FinancialYearDetailView.as_view(), name="financial-year-detail")
]
