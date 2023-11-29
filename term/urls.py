# urls.py

from django.urls import path

from .views import TermListView, TermDetailView, TermCreateView

urlpatterns = [
    path('create', TermCreateView.as_view(), name="term-create"),
    path('list', TermListView.as_view(), name="term-list"),
    path('<str:pk>', TermDetailView.as_view(), name="term-detail")
]
