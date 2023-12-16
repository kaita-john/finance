# urls.py

from django.urls import path

from .views import StaffListView, StaffDetailView, StaffCreateView

urlpatterns = [
    path('create', StaffCreateView.as_view(), name="staff-create"),
    path('list', StaffListView.as_view(), name="staff-list"),
    path('<str:pk>', StaffDetailView.as_view(), name="staff-detail")
]
