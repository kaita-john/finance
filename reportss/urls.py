# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('student-balance-list', ReportStudentBalanceView.as_view(), name="student-balance-list"),
    path('filter-students', FilterStudents.as_view(), name="filter-students"),
    path('student-transactions/<str:pk>', StudentTransactionsPrint.as_view(), name="student-transactions"),
]

