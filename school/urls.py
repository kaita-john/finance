# project/views.py
from django.http import JsonResponse, Http404
from django.urls import path
from rest_framework.response import Response

from .views import SchoolCreateView, SchoolListView, SchoolDetailView

urlpatterns = [
    path('create', SchoolCreateView.as_view(), name="school-create"),
    path('list', SchoolListView.as_view(), name="school-list"),
    path('<str:pk>', SchoolDetailView.as_view(), name="school-detail"),
]
