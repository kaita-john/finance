# urls.py

from django.urls import path

from .views import SchoolTypeListView, SchoolTypeDetailView, SchoolTypeCreateView

urlpatterns = [
    path('create', SchoolTypeCreateView.as_view(), name="schooltype-create"),
    path('list', SchoolTypeListView.as_view(), name="schooltype-list"),
    path('<str:pk>', SchoolTypeDetailView.as_view(), name="schooltype-detail")
]
