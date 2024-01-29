# urls.py

from django.urls import path

from .views import MpesaconfigListView, MpesaconfigDetailView, MpesaconfigCreateView

urlpatterns = [
    path('create', MpesaconfigCreateView.as_view(), name="mpesaconfig-create"),
    path('list', MpesaconfigListView.as_view(), name="mpesaconfig-list"),
    path('<str:pk>', MpesaconfigDetailView.as_view(), name="mpesaconfig-detail")
]
