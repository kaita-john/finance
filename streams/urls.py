# urls.py

from django.urls import path

from .views import StreamsListView, StreamsDetailView, StreamsCreateView

urlpatterns = [
    path('create', StreamsCreateView.as_view(), name="streams-create"),
    path('list', StreamsListView.as_view(), name="streams-list"),
    path('<str:pk>', StreamsDetailView.as_view(), name="streams-detail")
]
