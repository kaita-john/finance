# urls.py

from django.urls import path

from .views import *

urlpatterns = [

    path('student-balance-list', ReportStudentBalanceView.as_view(), name="student-balance-list"),
    path('filter-students', FilterStudents.as_view(), name="filter-students"),
    path('student-transactions/<str:pk>', StudentTransactionsPrint.as_view(), name="student-transactions"),
    path('student-collection-list/<str:pk>', StudentCollectionListView.as_view(), name="student-collection-list"),

    path('summary/income-summary', IncomeSummaryView.as_view(), name="income-summary"),
    path('summary/expense-summary', ExpenseSummaryView.as_view(), name="expense-summary"),
    path('summary/received-cheques', ReceivedChequesView.as_view(), name="received-cheques"),

    path('financial/cash-book', CashBookView.as_view(), name="income-summary"),
    path('financial/fee-register', FeeRegisterView.as_view(), name="income-summary"),

]

