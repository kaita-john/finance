# urls.py

from django.urls import path

from .views import RoleListView, RoleDetailView, RoleCreateView

urlpatterns = [
    path('create', RoleCreateView.as_view(), name="role-create"),
    path('list', RoleListView.as_view(), name="role-list"),
    path('<str:pk>', RoleDetailView.as_view(), name="role-detail")
]
