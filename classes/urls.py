# urls.py

from django.urls import path

from .views import ClassesListView, ClassesDetailView, ClassesCreateView

urlpatterns = [
    path('create', ClassesCreateView.as_view(), name="classes-create"),
    path('list', ClassesListView.as_view(), name="classes-list"),
    path('<str:pk>', ClassesDetailView.as_view(), name="classes-detail")
]
