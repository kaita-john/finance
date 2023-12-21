# Create your views here.

from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils import SchoolIdMixin, UUID_from_PrimaryKey
from .models import SchoolImage
from .serializers import FileUploadSerializer


# views.py

class FileUploadCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        #title = self.request.GET.get('title')
        # title = request.POST.get('title')
        # if not title:
        #     return Response({"details": "Title not provided"}, status=status.HTTP_400_BAD_REQUEST)

        # queryset = SchoolImage.objects.filter(school_id=school_id, title="logo")
        # if queryset:
        #     return Response({"detail": "Image already uploaded"}, status=status.HTTP_200_OK)


        documents = []
        with transaction.atomic():
            for k, v in request.data.items():
                for f in request.FILES.getlist(str(k)):
                    try:
                        original_file_name = f.name
                        ext = original_file_name.split('.')[1].strip().lower()
                        instance = SchoolImage.objects.create(
                            document=f,
                            creator=request.user,
                            original_file_name=original_file_name,
                            school_id = school_id,
                            title = "title"
                        )
                        exts = ['xlsx', 'csv']
                    except PermissionError:
                        return Response({"details": "Could not upload file"}, status=status.HTTP_400_BAD_REQUEST)
                    documents.append(str(instance.id))

            if not documents: return Response(
                {"details": "No files uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )

            details = {
                "message": "Upload was successful",
                "id": documents[0]
            }
            return Response({"detail": details}, status=status.HTTP_200_OK)




class SchoolImageListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return SchoolImage.objects.none()
        queryset = SchoolImage.objects.filter(school_id=school_id, title="logo")
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({"detail": serializer.data}, safe=False)





class SchoolImageDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = SchoolImage.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return SchoolImage.objects.get(id=id)
        except (ValueError, SchoolImage.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_update(serializer)
            return Response({'detail': 'Currency updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Record deleted successfully'}, status=status.HTTP_200_OK)
