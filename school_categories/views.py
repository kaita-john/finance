# Create your views here.
import uuid

from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils import SchoolIdMixin, IsSuperUser, UUID_from_PrimaryKey
from .models import SchoolCategory
from .serializers import SchoolCategorySerializer


class SchoolCategoryCreateView(generics.CreateAPIView):
    serializer_class = SchoolCategorySerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'detail': 'SchoolCategory created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SchoolCategoryListView(generics.ListAPIView):
    serializer_class = SchoolCategorySerializer
    queryset = SchoolCategory.objects.all()
    permission_classes = [IsAuthenticated, IsSuperUser]


class SchoolCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SchoolCategory.objects.all()
    serializer_class = SchoolCategorySerializer
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return SchoolCategory.objects.get(id=id)
        except (ValueError, SchoolCategory.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'detail': 'SchoolCategory updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Record deleted successfully'}, status=status.HTTP_200_OK)
