# views.py
import uuid

from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from school.models import School
from school.serializer import SchoolSerializer, SchoolCreateSerializer
from utils import IsAdminOrSuperUser


class SchoolCreateView(generics.CreateAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]  # Use the custom permission class
    #print("Here")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Combine first_name and last_name to create fullname
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')
            serializer.validated_data['contact_fullname'] = f"{first_name} {last_name}"

            self.perform_create(serializer)
            return Response({'detail': 'School created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SchoolListView(generics.ListAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            print("User is superuser")
            return School.objects.all()
        else:
            print(f"User is not superuser {user}")

        if user.school_id:
            return School.objects.filter(id=user.school_id.id)
        return School.objects.none()

class SchoolDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = uuid.UUID(primarykey)
            return School.objects.get(id=id)
        except (ValueError, School.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'detail': 'School Updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'School deleted successfully'}, status=status.HTTP_200_OK)

