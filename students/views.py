# Create your views here.
from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic_year.models import AcademicYear
from academic_year.serializers import AcademicYearSerializer
from appcollections.models import Collection
from invoices.models import Invoice
from invoices.views import createInvoices
from payment_in_kind_Receipt.models import PIKReceipt
from receipts.models import Receipt
from term.models import Term
from utils import SchoolIdMixin, UUID_from_PrimaryKey, currentAcademicYear, currentTerm, IsAdminOrSuperUser
from voteheads.models import VoteHead
from voteheads.serializers import VoteHeadSerializer
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
                    return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

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


        total_amount_required = Invoice.objects.filter(term=current_term, year=current_academic_year,student = student.id).aggregate(total_amount_required=Sum('amount'))['total_amount_required'] or 0.0
        total_amount_paid = Receipt.objects.filter(student_id=student.id,term=current_term, year=current_academic_year, is_reversed=False).aggregate(total_amount_paid=Sum('totalAmount'))['total_amount_paid'] or 0.0
        balance = total_amount_required - Decimal(total_amount_paid)

        response_data = {
            'student_id': student.id,
            'balance': balance,
        }

        return Response({"detail": response_data})


class StudentSearchByAdmissionNumber(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        admissionNumber = request.GET.get('admission')

        if not admissionNumber:
            return Response({'detail': "Admission Number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(admission_number=admissionNumber)
        except ObjectDoesNotExist:
            return Response({'detail': "Student with admission number not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentSerializer(student)
        serialized_data = serializer.data

        return Response({'detail': serialized_data}, status=status.HTTP_200_OK)


class GetStudentsByClass(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        currentClass = request.GET.get('currentClass')

        if not currentClass:
            return Response({'detail': "Current Class is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            students = Student.objects.filter(current_Class=currentClass).all()
        except Exception as exception:
            return Response({'detail': f"{exception}"}, status=status.HTTP_400_BAD_REQUEST)

        if not students:
            return JsonResponse([], status=200)

        for student in students:
            student.school_id = school_id

        serializer = StudentSerializer(students, many=True)
        serialized_data = serializer.data

        return Response({'detail': serialized_data}, status=status.HTTP_200_OK)


class GetStudentInvoicedVotehead(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        student = self.get_object()

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        year = request.GET.get('year')
        term = request.GET.get('term')

        current_academic_year = currentAcademicYear()
        current_term = currentTerm()
        if current_academic_year is None or current_term is None:
            return Response({'detail': 'Both Current Academic Year and Current Term must be set for school first'},
                            status=status.HTTP_200_OK)

        try:
            year = get_object_or_404(AcademicYear, id=year) if year else current_academic_year
            term = get_object_or_404(Term, id=term) if term else current_term
        except Exception as exception:
            return Response({'detail': exception}, status=status.HTTP_400_BAD_REQUEST)

        payload = []

        invoiceList = Invoice.objects.filter(
            student_id=student.id,
            term=term,
            year=year,
            school_id=school_id
        )

        for invoice in invoiceList:
            votehead = invoice.votehead
            receiptAmount = Collection.objects.filter(receipt__term=term, receipt__year=year, votehead=votehead, school_id=school_id,
                                      student=student).aggregate(Sum('amount'))['amount__sum']
            pikAmount = PIKReceipt.objects.filter(term=term, year=year, school_id=school_id, student=student).aggregate(
                Sum('totalAmount'))['totalAmount__sum']

            amountpaid = Decimal(pikAmount) + Decimal(receiptAmount)
            required_amount  = invoice.amount - amountpaid
            invoiced_amount = invoice.amount

            payload.append(
                {
                    "votehead": VoteHeadSerializer(votehead).data,
                    "name": votehead.vote_head_name,
                    "amount_paid": amountpaid,
                    "required_amount": required_amount,
                    "invoiced_amount": invoiced_amount,
                }
            )


        return Response({"detail": payload})

