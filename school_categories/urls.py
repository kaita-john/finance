# urls.py

from django.urls import path

from .views import SchoolCategoryListView, SchoolCategoryDetailView, SchoolCategoryCreateView

urlpatterns = [
    path('create', SchoolCategoryCreateView.as_view(), name="schoolcategory-create"),
    path('list', SchoolCategoryListView.as_view(), name="schoolcategory-list"),
    path('<str:pk>', SchoolCategoryDetailView.as_view(), name="schoolcategory-detail")
]
