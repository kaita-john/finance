# urls.py

from django.urls import path

from .views import *

urlpatterns = [

    path('student-balance-list', ReportStudentBalanceView.as_view(), name="student-balance-list"),

]

