# Create your views here.
import uuid
from collections import defaultdict
from uuid import UUID

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Sum, F
from django.http import JsonResponse, request
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic_year.models import AcademicYear
from classes.models import Classes
from classes.serializers import ClassesSerializer
from currencies.models import Currency
from fee_structures.models import FeeStructure
from fee_structures_items.models import FeeStructureItem
from schoolgroups.models import SchoolGroup
from students.models import Student
from term.models import Term
from term.serializers import TermSerializer
from utils import SchoolIdMixin, generate_unique_code, UUID_from_PrimaryKey, IsAdminOrSuperUser, currentAcademicYear, \
    DefaultMixin, currentTerm
from voteheads.models import VoteHead
from .models import Invoice
from .serializers import InvoiceSerializer, StructureSerializer, UninvoiceStudentSerializer


class InvoiceCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_create(serializer)
            return Response({'detail': 'Invoice created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class InvoiceListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()
        self.check_defaults(self.request, school_id)
        queryset = Invoice.objects.filter(school_id=school_id)

        term = self.request.query_params.get('term', None)
        academic_year = self.request.query_params.get('academic_year', None)
        totals = True
        student = self.request.query_params.get('student', None)


        getcurrentTerm = currentTerm(school_id)
        getcurrentAcademicYear = currentAcademicYear(school_id)
        if not term or term == "" or term == "null":
            term = getcurrentTerm.id
        if not academic_year or academic_year == "" or academic_year == "null":
            academic_year = getcurrentAcademicYear.id


        if term and term != "" and term != "null":
            queryset = queryset.filter(term = term)

        if academic_year and academic_year != "" and academic_year != "null":
            queryset = queryset.filter(year = academic_year)

        if student and student != "" and student != "null":
            totals = False
            if totals and totals != "" and totals != "null":
                raise ValueError(f"You cannot filter by both totals and student")
            queryset = queryset.filter(student = student)
            

        if totals and totals != "" and totals != "null":
            if student and student != "" and student != "null":
                raise ValueError(f"You cannot filter by both totals and student")

            grouped_by_student = defaultdict(list)
            for instance in queryset:
                student_id = instance.student.id
                grouped_by_student[student_id].append(instance)

            result = []
            for student_id, instances in grouped_by_student.items():
                total_amount = sum(instance.amount for instance in instances)
                first_instance = instances[0]
                first_instance.amount = total_amount
                result.append(first_instance)
                queryset = result

        return queryset


    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            if not queryset:
                return JsonResponse([], safe=False, status=200)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return JsonResponse(serializer.data, safe=False)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
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
        self.check_defaults(self.request, school_id)

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
        self.check_defaults(self.request, school_id)

        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Record deleted successfully'}, status=status.HTTP_200_OK)






def createInvoices(school_id, students, structure_year, structure_term, structure_class):
    try:
        currency = Currency.objects.get(is_default=True, school=school_id)
    except Currency.DoesNotExist:
        currency = None
        return Response({"detail": "Student not invoiced! Default Currency not set for this school"}, status=status.HTTP_400_BAD_REQUEST)

    fee_structures_itemList = FeeStructureItem.objects.filter(
        fee_Structure__academic_year__id=structure_year,
        fee_Structure__classes__id=structure_class,
        fee_Structure__term__id=structure_term,
        school_id=school_id
    )

    errors = []

    print(f"Length of fee structure items is {len(fee_structures_itemList)}")

    if not fee_structures_itemList:
        error_message = f"There are no Fee Structure Items for Academic Year {structure_year}, Term {structure_term} and Class {structure_class}"
        print(error_message)
        errors.append(error_message)

    if not students:
        error_message = "There are no students for selected students Group"
        print(f"Student List is empty")
        print(error_message)
        errors.append(error_message)

    if errors:
        return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

    invoice_no = generate_unique_code()

    with transaction.atomic():
        for student in students:
            boarding_status = student.boarding_status

            for item in fee_structures_itemList:
                try:
                    if item.votehead:
                        description = item.votehead.vote_head_name
                        amount = item.amount
                        term = item.fee_Structure.term
                        year = item.fee_Structure.academic_year
                        classes = item.fee_Structure.classes
                        school_id = item.school_id
                        votehead = item.votehead
                        required_boardingstatus = item.boardingStatus

                        if required_boardingstatus == boarding_status:
                            exists_query = Invoice.objects.filter(school_id=school_id, votehead__id=votehead.id, term=term, year=year, student=student, classes = structure_class)

                            if exists_query.exists():
                                print(f"Stopped and Student is {student} and Fee structure Class is {classes} and student class is {student.current_Class} and Votehead is {votehead.vote_head_name}")

                                print("Invoice already exists there!")
                                invoice = exists_query[0]
                                invoice.amount = invoice.amount + Decimal(amount)
                                invoice.save()
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
                                invoice.save()

                except Exception as e:
                    error_message = f"An error occurred while processing item {item.id} for student {student.id}: {e}"
                    print(error_message)
                    errors.append(error_message)

    if errors:
        return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"detail": "Invoicing was successful"}, status=status.HTTP_201_CREATED)





class InvoiceStructureView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    serializer_class = StructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        try:
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
            self.check_defaults(self.request, school_id)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serialized_data = serializer.data

            filter_type = serialized_data.get('filter_type')
            structure_year = serialized_data.get('structure_year')
            structure_term = serialized_data.get('structure_term')
            structure_class = serialized_data.get('structure_class')

            if filter_type and filter_type == 'student':
                student = serialized_data.get('student')
                if not student:
                    return Response({"detail": "Student ID is required for filter_type 'student'"})
                students = Student.objects.filter(id = student, school_id=school_id)

                return createInvoices(school_id, students, structure_year, structure_term, structure_class)


            elif filter_type and filter_type == 'class':
                classes = serialized_data.get('classes')
                if not classes:
                    return Response({"detail": "Class ID is required for filter_type 'class'"})
                students = Student.objects.filter(current_Class__id = classes, school_id=school_id)

                return createInvoices(school_id, students, structure_year, structure_term, structure_class)


            elif filter_type and filter_type == 'stream':
                classes =serialized_data.get('classes')
                stream =serialized_data.get('stream')
                if not classes or not stream:
                    return Response({"detail": "Both class ID and stream ID are required for filter_type 'stream'"})
                students = Student.objects.filter(current_Class__id = classes, current_Stream__id = stream, school_id=school_id)

                return createInvoices(school_id, students, structure_year, structure_term, structure_class)


            elif filter_type and filter_type == 'group':
                group =serialized_data.get('group')
                groupid = group
                if not groupid:
                    return Response({"detail": "Group is require for Group Query"})
                try:
                    group = SchoolGroup.objects.get(id=groupid)
                except SchoolGroup.DoesNotExist:
                    return Response({'detail': f"Invalid Group ID"}, status=status.HTTP_400_BAD_REQUEST)

                students = Student.objects.filter(current_Class__id=structure_class, groups__icontains=str(groupid),school_id=school_id)

                return createInvoices(school_id, students, structure_year, structure_term, structure_class)


            else:
                return Response({"detail": "Invalid filter_type. It should be one of: 'student', 'class', 'stream'"})

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceClassesListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = ClassesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()
        self.check_defaults(self.request, school_id)

        structure_year = self.request.GET.get('structure_year')
        structure_term = self.request.GET.get('structure_term')
        
        if not structure_term or structure_term == "" or structure_year == "null"  or structure_term == "null" or not structure_year or structure_year == "":
            return Response({'detail': f"Both Structure Term and Year are required"}, status=status.HTTP_400_BAD_REQUEST)

        if structure_year and structure_year != "" and structure_year != "null":
            try:
                structure_year = UUID(structure_year)
                if not Invoice.objects.filter(school_id=school_id, year=structure_year).exists():
                    raise ValidationError({"detail": "Invalid structure_year"})
            except ValueError:
                raise ValidationError({"detail": "Invalid UUID for structure_year"})

        if structure_term and structure_term != "" and structure_term != "null":
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







class UnInvoiceStudentView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    serializer_class = UninvoiceStudentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def post(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

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





class TotalInvoicedAmount(APIView, DefaultMixin, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

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







class invoiceView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request, *args, **kwargs):
        print("called")
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Invoice.objects.none()
        self.check_defaults(self.request, school_id)

        academic_year = self.request.GET.get('academic_year')

        if not academic_year:
            academic_year = currentAcademicYear(school_id)
            if not academic_year:
                Response({'detail': "Default Academic Year Not Set For This School"},status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                academic_year = AcademicYear.objects.get(id=academic_year)
            except ObjectDoesNotExist:
                return Response({'detail': f"Academic Year does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        fullList = []

        feeStructureItems = FeeStructureItem.objects.filter(school_id=school_id, fee_Structure__academic_year=academic_year)
        unique_terms = Term.objects.filter(fee_structures__fee_structure_items__in=feeStructureItems
        ).distinct()
        terms_list = unique_terms

        for term in terms_list:
            print(term.term_name)
            term_name = term.term_name
            start_date = term.begin_date
            end_date = term.end_date

            overall_amount = Decimal(0.0)
            feeStructures = FeeStructure.objects.filter(school_id=school_id,academic_year=academic_year,term=term)

            unique_classes_list = []

            for feeStructure in feeStructures:
                structureYear = feeStructure.academic_year

                thevotehead_list = feeStructure.fee_structure_items.values_list('votehead', flat=True).distinct()
                items = feeStructure.fee_structure_items.all()

                fee_structure_items = {}
                votehead_list = defaultdict(lambda: defaultdict(Decimal))
                overall = defaultdict(Decimal)

                invoiced_voteheads_list = []

                for item in items:
                    boarding_status = item.boardingStatus
                    votehead_list[item.votehead.vote_head_name][boarding_status] += Decimal(item.amount)
                    overall[boarding_status] += Decimal(item.amount)
                    data =  {
                        "votehead": item.votehead.vote_head_name,
                        "boardingStatus": boarding_status,
                        "amount": Decimal(item.amount)
                    }
                    invoiced_voteheads_list.append(data)

                fee_structure_items['invoiced_voteheads'] = invoiced_voteheads_list
                fee_structure_items['totals'] = overall

                overall_amount += sum(overall.values())

                class_info = (
                    feeStructure.classes.id,
                    feeStructure.classes.classname,
                    feeStructure.classes.graduation_year,
                    feeStructure.classes.graduation_month,
                    feeStructure.academic_year.id,
                    feeStructure.classes.school_id,
                    fee_structure_items
                )

                # Append the class_info to the list
                unique_classes_list.append(class_info)

            # Filter out duplicate classes based on class id
            unique_classes_list = {class_info[0]: class_info for class_info in unique_classes_list}.values()

            classes_list = [
                {
                    "id": class_info[0],
                    "classname": class_info[1],
                    "graduation_year": class_info[2],
                    "graduation_month": class_info[3],
                    "academic_year_id": class_info[4],
                    "school_id": class_info[5],
                    "fee_structure_items": dict(class_info[6]),
                }
                for class_info in unique_classes_list
            ]

            theobject = {
                "term_details": TermSerializer(term).data,
                "class_details": classes_list,
                "overall_amount": overall_amount
            }

            fullList.append(theobject)

        return Response({'detail': fullList}, status=status.HTTP_200_OK)
