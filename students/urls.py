# urls.py

from django.urls import path

from .views import StudentListView, StudentDetailView, StudentCreateView, StudentBalanceDetailView

urlpatterns = [
    path('create', StudentCreateView.as_view(), name="student-create"),
    path('list', StudentListView.as_view(), name="student-list"),
    path('balance/<str:pk>', StudentBalanceDetailView.as_view(), name="student-current-balance"),
    path('<str:pk>', StudentDetailView.as_view(), name="student-detail")
]
