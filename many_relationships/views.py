# Create your views here.
import uuid

from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils import SchoolIdMixin, IsAdminOrSuperUser, UUID_from_PrimaryKey
from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.create_fee_structure(serializer.validated_data)
            return Response({'detail': f'Vehicle created successfully\n{serializer.data}'}, status=status.HTTP_201_CREATED)
        else:
            print(f'The fee structure items is ')

            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def create_fee_structure(self, validated_data):
        try:
            with transaction.atomic():
                fee_structure_items_data = validated_data.pop('fee_structure_items', [])
                fee_structure = Vehicle.objects.create(**validated_data)

                print(f'The fee structure items is {fee_structure_items_data}')

                for fee_structure_item_data in fee_structure_items_data:
                    fee_structure_item_data['school_id'] = fee_structure.school_id
                    fee_structure_item_data['fee_structure'] = fee_structure.id
                    fee_structure_item_serializer = VehicleSerializer(data=fee_structure_item_data)

                    if fee_structure_item_serializer.is_valid():
                        fee_structure_item_serializer.save()
                        fee_structure.fee_structure_items.add(fee_structure_item_serializer.instance)
                    else:
                        print("Found Error")
                        raise Exception(fee_structure_item_serializer.errors)

            return fee_structure
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class VehicleListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Vehicle.objects.none()
        queryset = Vehicle.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class VehicleDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Vehicle.objects.get(id=id)
        except (ValueError, Vehicle.DoesNotExist):
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

            # Create or update associated VehicleItem instances
            fee_structure_items_data = request.data.get('fee_structure_items', [])
            fee_structure_items_serializer = VehicleItemSerializer(data=fee_structure_items_data, many=True)
            if fee_structure_items_serializer.is_valid():
                fee_structure_items_serializer.save(fee_structure=instance)
            else:
                return Response({'detail': fee_structure_items_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            self.perform_update(serializer)

            return Response({'detail': 'Fee Structure updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

