# urls.py

from django.urls import path

from .views import SchoolGroupListView, SchoolGroupDetailView, SchoolGroupCreateView

urlpatterns = [
    path('create', SchoolGroupCreateView.as_view(), name="school-group-create"),
    path('list', SchoolGroupListView.as_view(), name="school-group-list"),
    path('<str:pk>', SchoolGroupDetailView.as_view(), name="school-group-detail")
]
