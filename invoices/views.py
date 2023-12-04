# Create your views here.
from uuid import UUID

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from classes.models import Classes
from classes.serializers import ClassesSerializer
from currencies.models import Currency
from fee_structures_items.models import FeeStructureItem
from students.models import Student
from utils import SchoolIdMixin, generate_unique_code, UUID_from_PrimaryKey
from .models import Invoice
from .serializers import InvoiceSerializer, StructureSerializer


class InvoiceCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()
        queryset = Invoice.objects.filter(school_id=school_id)
        return queryset
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)


class InvoiceDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

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

    fee_structures_itemList = FeeStructureItem.objects.filter(
        fee_Structure__academic_year=structure_year,
        fee_Structure__classes=structure_class,
        fee_Structure__term=structure_term
    )

    errors = []

    with transaction.atomic():
        for student in students:
            for item in fee_structures_itemList:
                description = item.votehead.vote_head_name
                invoice_no = generate_unique_code()
                amount = item.amount
                term = item.fee_Structure.term
                year = item.fee_Structure.academic_year
                classes = item.fee_Structure.classes
                school_id = item.school_id

                # Create the Invoice object
                invoice = Invoice(
                    issueDate=timezone.now().date(),
                    invoiceNo=invoice_no,
                    amount=amount,
                    paid=amount,
                    due=amount,
                    description=description,
                    student=student,
                    term=term,
                    year=year,
                    classes=classes,
                    currency=currency,
                    school_id=school_id
                )

                try:
                    invoice.save()
                except Exception as e:
                    error_message = f"An error occurred while saving the invoice for student {student.id}: {e}"
                    print(error_message)
                    errors.append(error_message)

    if errors:
        return Response({"errors": errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({"detail": "Invoicing was successful"}, status=status.HTTP_201_CREATED)



class InvoiceStructureView(generics.GenericAPIView):
    serializer_class = StructureSerializer

    def post(self, request, *args, **kwargs):
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
            students = Student.objects.filter(id = student)

            return createInvoices(students, structure_year, structure_term, structure_class)


        elif filter_type == 'class':
            class_id = serialized_data.get('classes')
            if not class_id:
                return Response({"detail": "Class ID is required for filter_type 'class'"})
            students = Student.objects.filter(current_Class = structure_class)

            return createInvoices(students, structure_year, structure_term, structure_class)


        elif filter_type == 'stream':
            classes =serialized_data.get('classes')
            stream =serialized_data.get('stream')
            if not classes or not stream:
                return Response({"detail": "Both class ID and stream ID are required for filter_type 'stream'"})
            students = Student.objects.filter(current_Class = structure_class, current_Stream = stream)

            return createInvoices(students, structure_year, structure_term, structure_class)


        else:
            return Response({"detail": "Invalid filter_type. It should be one of: 'student', 'class', 'stream'"})






class InvoiceClassesListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = ClassesSerializer
    permission_classes = [IsAuthenticated]

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
            return Response([], status=200)

        unique_classes = set(queryset.values_list('classes', flat=True))
        class_instances = Classes.objects.filter(id__in=unique_classes)
        serializer = self.get_serializer(class_instances, many=True)

        return Response({"detail": serializer.data}, status=200)

