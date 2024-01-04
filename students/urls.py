# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('create', StudentCreateView.as_view(), name="student-create"),
    path('upload', UploadStudentCreateView.as_view(), name="student-create"),
    path('list', StudentListView.as_view(), name="student-list"),
    path('search-by-admission', StudentSearchByAdmissionNumber.as_view(), name="student-list"),
    path('get-student-by-class', GetStudentsByClass.as_view(), name="get-student-by-class"),
    path('get-invoiced-voteheads/<str:pk>', GetStudentInvoicedVotehead.as_view(), name="get-invoiced-voteheads"),
    path('balance/<str:pk>', StudentBalanceDetailView.as_view(), name="student-current-balance"),
    path('<str:pk>', StudentDetailView.as_view(), name="student-detail")
]
