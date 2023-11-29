# urls.py

from django.urls import path

from .views import VoteHeadListView, VoteHeadDetailView, VoteHeadCreateView

urlpatterns = [
    path('create', VoteHeadCreateView.as_view(), name="votehead-create"),
    path('list', VoteHeadListView.as_view(), name="votehead-list"),
    path('<str:pk>', VoteHeadDetailView.as_view(), name="votehead-detail")
]
