# urls.py

from django.urls import path

from .views import *

urlpatterns = [
    path('create', BursaryCreateView.as_view(), name="bursary-create"),
    path('list', BursaryListView.as_view(), name="bursary-list"),
    path('post/<str:pk>', PostBursaryDetailView.as_view(), name="bursary-detail"),
    path('unpost/<str:pk>', UnPostBursaryDetailView.as_view(), name="bursary-detail"),
    path('trash/<str:pk>', TrashBursaryDetailView.as_view(), name="trashBursaryDetailView-detail"),
    path('<str:pk>', BursaryDetailView.as_view(), name="bursary-detail")
]
