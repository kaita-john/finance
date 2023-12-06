# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('uploadwebfile', FileUploadWebView, name="upload-file"),
]
