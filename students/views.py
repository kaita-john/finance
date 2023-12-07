# Create your views here.

from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from invoices.models import Invoice
from invoices.views import createInvoices
from utils import SchoolIdMixin, UUID_from_PrimaryKey, currentAcademicYear, currentTerm
from .models import Student
from .serializers import StudentSerializer


class StudentCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_create(serializer)

            created_student = serializer.instance
            if created_student.invoice_Student:
                studentList = []
                studentList.append(created_student)

                try:
                    return createInvoices(studentList, created_student.current_Year, created_student.current_Term,
                                          created_student.current_Class)
                except Exception as exception:
                    return Response({'detail': exception}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'detail': 'Student created successfully'}, status=status.HTTP_201_CREATED)

        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class StudentListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Student.objects.none()
        queryset = Student.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)


class StudentDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Student.objects.get(id=id)
        except (ValueError, Student.DoesNotExist):
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
            return Response({'detail': 'Student updated successfully'}, status=status.HTTP_201_CREATED)
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


class StudentBalanceDetailView(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        student = self.get_object()

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        current_academic_year = currentAcademicYear()
        current_term = currentTerm()
        if current_academic_year is None or current_term is None:
            return Response({'detail': 'Both Current Academic Year and Current Term must be set for school first'}, status=status.HTTP_200_OK)

        total_amount = Invoice.objects.filter(
            student_id=student.id,
            term=current_term,
            year=current_academic_year,
            school_id=school_id
        ).aggregate(Sum('due'))['due__sum']

        total_invoice_amount = total_amount or 0.00
        response_data = {
            'student_id': student.id,
            'balance': total_invoice_amount,
        }

        return Response({"detail": response_data})
