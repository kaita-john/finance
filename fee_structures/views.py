# Create your views here.

from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from fee_structures_items.models import FeeStructureItem
from fee_structures_items.serializers import FeeStructureItemSerializer
from utils import SchoolIdMixin, IsAdminOrSuperUser, UUID_from_PrimaryKey, currentAcademicYear, DefaultMixin
from .models import FeeStructure
from .serializers import FeeStructureSerializer


class FeeStructureCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            academic_year = serializer.validated_data.get('academic_year', None)
            if academic_year is None:
                current_academic_year = currentAcademicYear(school_id)
                if current_academic_year is None:
                    return Response({'detail': 'Current academic year is not set'}, status=status.HTTP_400_BAD_REQUEST)
                serializer.validated_data['academic_year'] = current_academic_year

            try:
                with transaction.atomic():
                    fee_structure_items_data = serializer.validated_data.pop('fee_structure_values', [])
                    fee_structure = serializer.save()
                    for fee_structure_item_data in fee_structure_items_data:
                        fee_structure_item_data['school_id'] = fee_structure.school_id
                        fee_structure_item_data['fee_Structure'] = fee_structure.id
                        print(f"checking -> {fee_structure_item_data}")
                        fee_structure_item_serializer = FeeStructureItemSerializer(data=fee_structure_item_data)
                        fee_structure_item_serializer.is_valid(raise_exception=True)
                        print(f"checking -> {fee_structure_item_serializer.validated_data}")
                        fee_structure_item_serializer.save()

                    return Response({'detail': f'FeeStructure created successfully'},status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("Here")
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FeeStructureListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return FeeStructure.objects.none()
        self.check_defaults(self.request, school_id)

        queryset = FeeStructure.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class FeeStructureDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return FeeStructure.objects.get(id=id)
        except (ValueError, FeeStructure.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            FeeStructureItem.objects.filter(fee_structure=instance).delete()
            fee_structure_items_data = serializer.validated_data.get('fee_structure_values', [])
            fee_structure = serializer.save()

            for fee_structure_item_data in fee_structure_items_data:
                fee_structure_item_data['school_id'] = fee_structure.school_id
                fee_structure_item_data['fee_Structure'] = fee_structure.id
                fee_structure_item_serializer = FeeStructureItemSerializer(data=fee_structure_item_data)
                fee_structure_item_serializer.is_valid(raise_exception=True)
                fee_structure_item_serializer.save()

            self.perform_update(serializer)

            return Response({'detail': 'Fee Structure updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def delete(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Fee structure item deleted successfully!'}, status=status.HTTP_200_OK)