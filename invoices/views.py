# Create your views here.
import uuid
from uuid import UUID

from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from classes.models import Classes
from classes.serializers import ClassesSerializer
from currencies.models import Currency
from fee_structures_items.models import FeeStructureItem
from students.models import Student
from utils import SchoolIdMixin, generate_unique_code, UUID_from_PrimaryKey, IsAdminOrSuperUser
from .models import Invoice
from .serializers import InvoiceSerializer, StructureSerializer, UninvoiceStudentSerializer


class InvoiceCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_create(serializer)
            return Response({'detail': 'Invoice created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()

        common_records = Invoice.objects.filter(school_id=school_id).values('term', 'year', 'student').distinct()
        term = common_records['term']
        year = common_records['year']
        student_id = common_records['student']

        queryset = Invoice.objects.filter(school_id=school_id,term=term,year=year,student=student_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        amount = queryset.aggregate(Sum('amount'))['amount__sum']
        paid = queryset.aggregate(Sum('paid'))['paid__sum']
        due = queryset.aggregate(Sum('due'))['due__sum']

        queryset.amount = amount
        queryset.paid = paid
        queryset.due = due

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)


class InvoiceDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Invoice.objects.get(id=id)
        except (ValueError, Invoice.DoesNotExist):
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
            return Response({'detail': 'Invoice updated successfully'}, status=status.HTTP_201_CREATED)
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







def createInvoices(students, structure_year, structure_term, structure_class):
    try:
        currency = Currency.objects.get(is_default=True)
    except Currency.DoesNotExist:
        currency = None
        return Response({"detail": "Student not invoiced! Default Currency not set for this school"}, status=status.HTTP_400_BAD_REQUEST)


    fee_structures_itemList = FeeStructureItem.objects.filter(
        fee_Structure__academic_year=structure_year,
        fee_Structure__classes=structure_class,
        fee_Structure__term=structure_term
    )

    errors = []

    invoice_no = generate_unique_code()

    with transaction.atomic():
        for student in students:
            for item in fee_structures_itemList:
                description = item.votehead.vote_head_name
                amount = item.amount
                term = item.fee_Structure.term
                year = item.fee_Structure.academic_year
                classes = item.fee_Structure.classes
                school_id = item.school_id
                votehead = item.votehead

                exists_query = Invoice.objects.filter(
                    votehead__id=votehead.id,
                    term=term,
                    year=year,
                    student=student
                )

                if exists_query.exists():
                    pass
                else:
                    invoice = Invoice(
                        issueDate=timezone.now().date(),
                        invoiceNo=invoice_no,
                        amount=amount,
                        paid=0.00,
                        due=amount,
                        description=description,
                        student=student,
                        term=term,
                        year=year,
                        classes=classes,
                        currency=currency,
                        school_id=school_id,
                        votehead=votehead
                    )
                    try:
                        invoice.save()
                    except Exception as e:
                        error_message = f"An error occurred while saving the invoice for student {student.id}: {e}"
                        print(error_message)
                        errors.append(error_message)

    if errors:
        return Response({"detail": errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"detail": "Invoicing was successful"}, status=status.HTTP_201_CREATED)



class InvoiceStructureView(SchoolIdMixin, generics.GenericAPIView):
    serializer_class = StructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]


    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.data

        filter_type = serialized_data.get('filter_type')
        structure_year = serialized_data.get('structure_year')
        structure_term = serialized_data.get('structure_term')
        structure_class = serialized_data.get('structure_class')

        if filter_type == 'student':
            student = serialized_data.get('student')
            if not student:
                return Response({"detail": "Student ID is required for filter_type 'student'"})
            students = Student.objects.filter(id = student, school_id=school_id)

            return createInvoices(students, structure_year, structure_term, structure_class)


        elif filter_type == 'class':
            class_id = serialized_data.get('classes')
            if not class_id:
                return Response({"detail": "Class ID is required for filter_type 'class'"})
            students = Student.objects.filter(current_Class = structure_class, school_id=school_id)

            return createInvoices(students, structure_year, structure_term, structure_class)


        elif filter_type == 'stream':
            classes =serialized_data.get('classes')
            stream =serialized_data.get('stream')
            if not classes or not stream:
                return Response({"detail": "Both class ID and stream ID are required for filter_type 'stream'"})
            students = Student.objects.filter(current_Class = structure_class, current_Stream = stream, school_id=school_id)

            return createInvoices(students, structure_year, structure_term, structure_class)


        else:
            return Response({"detail": "Invalid filter_type. It should be one of: 'student', 'class', 'stream'"})






class InvoiceClassesListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = ClassesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()

        structure_year = self.request.GET.get('structure_year')
        structure_term = self.request.GET.get('structure_term')

        if structure_year:
            try:
                structure_year = UUID(structure_year)
                if not Invoice.objects.filter(school_id=school_id, year=structure_year).exists():
                    raise ValidationError({"detail": "Invalid structure_year"})
            except ValueError:
                raise ValidationError({"detail": "Invalid UUID for structure_year"})

        if structure_term:
            try:
                structure_term = UUID(structure_term)
                if not Invoice.objects.filter(school_id=school_id, term=structure_term).exists():
                    raise ValidationError({"detail": "Invalid structure_term"})
            except ValueError:
                raise ValidationError({"detail": "Invalid UUID for structure_term"})


        queryset = Invoice.objects.filter(school_id=school_id, year=structure_year, term=structure_term)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        unique_classes = set(queryset.values_list('classes', flat=True))
        class_instances = Classes.objects.filter(id__in=unique_classes)
        serializer = self.get_serializer(class_instances, many=True)

        return Response({"detail": serializer.data}, status=200)







class UnInvoiceStudentView(SchoolIdMixin, generics.GenericAPIView):
    serializer_class = UninvoiceStudentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.data

        structure_year = serialized_data.get('structure_year')
        structure_term = serialized_data.get('structure_term')
        structure_class = serialized_data.get('structure_class')
        structure_stream = serialized_data.get('structure_stream')
        student = serialized_data.get('student')
        filter_type = serialized_data.get('filter_type')

        invoicetypes = ["classes", "student", "stream"]
        if filter_type not in invoicetypes:
            return Response({'detail': "Valid options are class, student and stream"},status=status.HTTP_400_BAD_REQUEST)

        if filter_type == "stream" and structure_class is None or structure_term is None:
            return Response({'detail': "To uninvoice a stream, enter both Class and Term"},status=status.HTTP_400_BAD_REQUEST)

        size = None
        if filter_type == "classes":
            invoiceList = Invoice.objects.filter(year=structure_year, term=structure_term, classes=structure_class, school_id=school_id)
            size = len(invoiceList)
            for value in invoiceList:
                value.delete()
        elif filter_type == "stream":
            invoiceList = Invoice.objects.filter(year=structure_year, term=structure_term, classes=structure_class, student__current_Stream=structure_stream, school_id=school_id)
            size = len(invoiceList)
            for value in invoiceList:
                value.delete()
        elif filter_type == "student":
            invoiceList = Invoice.objects.filter(student=student)
            size = len(invoiceList)
            for value in invoiceList:
                value.delete()

        return Response({'detail': f'{size} records were uninvoiced. Successfully!'}, status=status.HTTP_201_CREATED)





class TotalInvoicedAmount(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        structure_year = request.GET.get('structure_year')
        structure_term = request.GET.get('structure_term')

        if not school_id or not structure_year or not structure_term:
            return Response({'detail': "Structure Term and Structure Year are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            school_id = uuid.UUID(school_id)
            structure_year = uuid.UUID(structure_year)
            structure_term = uuid.UUID(structure_term)
        except ValueError:
            return Response({'detail': "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Invoice.objects.filter(school_id=school_id, term=structure_term, year=structure_year)

        if not queryset.exists():
            return Response({'detail': 0.0}, status=status.HTTP_200_OK)

        total_sum = queryset.aggregate(Sum('amount'))['amount__sum']
        return Response({'detail': float(total_sum)}, status=status.HTTP_200_OK)
