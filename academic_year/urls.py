# urls.py

from django.urls import path

from .views import AcademicYearListView, AcademicYearDetailView, AcademicYearCreateView, CurrentAcademicYear

urlpatterns = [
    path('create', AcademicYearCreateView.as_view(), name="academic-year-create"),
    path('list', AcademicYearListView.as_view(), name="academic-year-list"),
    path('current', CurrentAcademicYear.as_view(), name="current-academicyear"),
    path('<str:pk>', AcademicYearDetailView.as_view(), name="academic-year-detail")
]
