# urls.py

from django.urls import path

from .views import ConfigurationListView, ConfigurationDetailView, ConfigurationCreateView

urlpatterns = [
    path('create', ConfigurationCreateView.as_view(), name="configuration-create"),
    path('list', ConfigurationListView.as_view(), name="configuration-list"),
    path('<str:pk>', ConfigurationDetailView.as_view(), name="configuration-detail")
]
