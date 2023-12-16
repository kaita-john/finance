# urls.py

from django.urls import path

from .views import VoteHeadListView, VoteHeadDetailView, VoteHeadCreateView
from .voteheadconfig_views import *

urlpatterns = [
    path('create-votehead-config', VoteheadConfigurationCreateView.as_view(), name="votehead-config-create"),
    path('list-votehead-config', VoteheadConfigurationListView.as_view(), name="votehead-config-list"),
    path('votehead-config/<str:pk>', VoteheadConfigurationDetailView.as_view(), name="votehead-config-detail"),
    path('create', VoteHeadCreateView.as_view(), name="votehead-create"),
    path('list', VoteHeadListView.as_view(), name="votehead-list"),
    path('<str:pk>', VoteHeadDetailView.as_view(), name="votehead-detail"),
]
