# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('create', MpesaconfigCreateView.as_view(), name="mpesaconfig-create"),
    path('list', MpesaconfigListView.as_view(), name="mpesaconfig-list"),
    path("callback", MpesaCallBackView.as_view(), name="callback"),
    path("register-validation-and-confirmation", RegisterMpesaValidationandCallBackView.as_view(), name="registerMpesaValidationandCallBackView"),
    path('<str:pk>', MpesaconfigDetailView.as_view(), name="mpesaconfig-detail")
]
