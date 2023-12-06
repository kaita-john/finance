# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('upload-file', FileUploadCreateView.as_view(), name='upload-file'),
    path('fetch-logo', SchoolImageListView.as_view(), name='upload-file'),
    path('<str:pk>', SchoolImageDetailView.as_view(), name="currency-detail")
]
