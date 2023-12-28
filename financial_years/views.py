# Create your views here.
import uuid

from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import SchoolIdMixin, IsAdminOrSuperUser, close_financial_year
from financial_years.models import FinancialYear
from .serializers import FinancialYearSerializer

class FinancialYearCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = FinancialYearSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school'] = school_id
            self.perform_create(serializer)
            return Response({'detail': 'Financial Year created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class FinancialYearListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = FinancialYearSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return FinancialYear.objects.none()
        queryset = FinancialYear.objects.filter(school=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class FinancialYearDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FinancialYear.objects.all()
    serializer_class = FinancialYearSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id =  uuid.UUID(primarykey)
            return FinancialYear.objects.get(id=id)
        except (ValueError, FinancialYear.DoesNotExist):
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
            return Response({'detail': 'Financial Year updated successfully'}, status=status.HTTP_201_CREATED)
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


class CloseFinancialYearView(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        current_financial_year = request.GET.get('current_financial_year')
        new_financial_year = request.GET.get('new_financial_year')

        if not current_financial_year or not new_financial_year:
            return Response({'detail': "Both current and new financial years are required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            school_id = uuid.UUID(school_id)
            current_financial_year = FinancialYear.objects.get(id = current_financial_year)
            new_financial_year = FinancialYear.objects.get(id = new_financial_year)
            close_financial_year(current_financial_year, new_financial_year, school_id)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': "Year Closed Successfully"}, status=status.HTTP_200_OK)
