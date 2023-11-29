# urls.py

from django.urls import path

from .views import StudentListView, StudentDetailView, StudentCreateView

urlpatterns = [
    path('create', StudentCreateView.as_view(), name="student-create"),
    path('list', StudentListView.as_view(), name="student-list"),
    path('<str:pk>', StudentDetailView.as_view(), name="student-detail")
]
