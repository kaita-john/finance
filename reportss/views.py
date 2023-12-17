# Create your views here.
from datetime import date, datetime

from _decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic_year.models import AcademicYear
from invoices.models import Invoice
from items.models import Item
from payment_in_kind_Receipt.models import PIKReceipt
from receipts.models import Receipt
from reportss.models import ReportStudentBalance, StudentTransactionsPrintView
from reportss.serializers import ReportStudentBalanceSerializer, StudentTransactionsPrintViewSerializer
from students.models import Student
from students.serializers import StudentSerializer
from term.models import Term
from utils import SchoolIdMixin, currentAcademicYear, currentTerm, IsAdminOrSuperUser


class ReportStudentBalanceView(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def calculate(self, queryset, startdate, enddate, boardingstatus, term, year):

        if boardingstatus:
            queryset.filter(boarding_status=boardingstatus)

        reportsStudentBalanceList = []

        current_academic_year = currentAcademicYear()
        current_term = currentTerm()

        if not year:
            return Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
        if not term:
            return Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            year = get_object_or_404(AcademicYear, id=year) if year else current_academic_year
            term = get_object_or_404(Term, id=term) if term else current_term
        except Exception as exception:
            pass

        for student in queryset:
            totalExpected = Decimal('0.0')
            totalPaid = Decimal('0.0')

            invoiceList = Invoice.objects.filter(term=term, year=year, student=student)
            if startdate:
                 invoiceList = invoiceList.filter(issueDate__gt=startdate)
            if enddate:
                invoiceList = invoiceList.filter(issueDate__lte=enddate)
            totalExpected += invoiceList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')


            receiptList = Receipt.objects.filter(term=term, year=year, student=student,is_reversed=False)
            if startdate:
                 receiptList = receiptList.filter(receipt_date__gt=startdate)
            if enddate:
                receiptList = receiptList.filter(receipt_date__lte=enddate)
            paid = receiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid


            pikReceiptList = PIKReceipt.objects.filter(term=term, year=year, student=student,is_posted=True)
            if startdate:
                 pikReceiptList = pikReceiptList.filter(receipt_date__gt=startdate)
            if enddate:
                pikReceiptList = pikReceiptList.filter(receipt_date__lte=enddate)
            paid = pikReceiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            bursaryItemList = Item.objects.filter(bursary__term=term, bursary__year=year,student=student, bursary__posted=True)
            if startdate:
                 bursaryItemList = bursaryItemList.filter(item_date__gt=startdate)
            if enddate:
                bursaryItemList = bursaryItemList.filter(item_date__lte=enddate)
            paid = bursaryItemList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            reportStudentBalance = ReportStudentBalance(
                admission_number=student.admission_number,
                name=f"{student.first_name} {student.last_name}",
                current_Class=student.current_Class,
                boarding_status=student.boarding_status,
                expected=totalExpected,
                paid=totalPaid,
                totalBalance=totalExpected - totalPaid,
                schoolFee=totalExpected
            )

            reportsStudentBalanceList.append(reportStudentBalance)
        return reportsStudentBalanceList



    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        queryset = Student.objects.all()

        currentClass = request.GET.get('currentClass')
        stream = request.GET.get('stream')
        student = request.GET.get('student')
        startdate = request.GET.get('startdate')
        enddate = request.GET.get('enddate')
        boardingstatus = request.GET.get('boardingstatus')
        amountabove = request.GET.get('amountabove')
        amountbelow = request.GET.get('amountbelow')
        term = request.GET.get('term')
        year = request.GET.get('year')

        reportsStudentBalanceList = []

        try:
            if not currentClass and not stream and not student:
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if currentClass:
                queryset = queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if stream:
                if not currentClass:
                    return Response({'detail': f"Both Class and Stream must be entered to query stream"}, status=status.HTTP_400_BAD_REQUEST)
                queryset =  queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if student:
                queryset = queryset.filter(id=student)
                print(f"student was passed {queryset}")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate,  boardingstatus, term, year)

            if amountbelow:
                amountbelow = Decimal(amountbelow)
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance < amountbelow]

            if amountabove:
                amountabove = Decimal(amountabove)
                print(f"Amount above was passed {reportsStudentBalanceList}")
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance > amountabove]

            serializer = ReportStudentBalanceSerializer(reportsStudentBalanceList, many=True)
            serialized_data = serializer.data
        except Exception as exception:
            return Response({'detail': exception}, status=status.HTTP_400_BAD_REQUEST)


        return Response({'detail': serialized_data}, status=status.HTTP_200_OK)




class FilterStudents(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    model = Student

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        currentClass = request.GET.get('currentClass')
        currentStream = request.GET.get('currentStream')
        admissionNumber = request.GET.get('admissionNumber')
        studentid = request.GET.get('studentid')

        queryset = Student.objects.all()

        try:

            if not currentClass or not currentStream or not admissionNumber:
                pass

            if studentid:
                queryset = queryset.filter(id = studentid)

            if admissionNumber:
                queryset = queryset.filter(admission_number = admissionNumber)

            if currentClass:
                queryset = queryset.filter(current_Class = currentClass)

            if currentStream:
                if not currentClass:
                    return Response({'detail': f"Please  student class"}, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(current_Stream = currentStream,  current_Class=currentClass)

            if not queryset:
                return JsonResponse([], status=200)

            for student in queryset:
                student.school_id = school_id

            serializer = StudentSerializer(queryset, many=True)
            serialized_data = serializer.data

            return Response({'detail': serialized_data}, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'detail': f"{exception}"}, status=status.HTTP_400_BAD_REQUEST)


class StudentTransactionsPrint(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):

        student = self.get_object()

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        startdate = request.GET.get('startdate')
        enddate = request.GET.get('enddate')
        term = request.GET.get('term')
        academicYear = request.GET.get('academicYear')


        querysetInvoices = Invoice.objects.filter(
            student_id=student.id,
            school_id=school_id
        )

        querysetReceipts = Receipt.objects.filter(
            student_id=student.id,
            school_id=school_id
        )

        querysetPIKReceipts = PIKReceipt.objects.filter(
            student_id=student.id,
            school_id=school_id
        )

        querysetBursaries = Item.objects.filter(
            student_id=student.id,
            school_id=school_id
        )

        if term:
            querysetInvoices = querysetInvoices.filter(term__id=term)
            querysetReceipts = querysetReceipts.filter(term__id=term)
            querysetPIKReceipts = querysetPIKReceipts.filter(term__id=term)
            querysetBursaries = querysetBursaries.filter(bursary__term__id=term)

        if academicYear:
            querysetInvoices = querysetInvoices.filter(year__id=academicYear)
            querysetReceipts = querysetReceipts.filter(year__id=academicYear)
            querysetPIKReceipts = querysetPIKReceipts.filter(year__id=academicYear)
            querysetBursaries = querysetBursaries.filter(bursary__year__id=academicYear)

        if startdate:
            querysetInvoices = querysetInvoices.filter(issueDate__gt = startdate)
            querysetReceipts = querysetReceipts.filter(transaction_date__gt = startdate)
            querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__gt = startdate)
            querysetBursaries = querysetBursaries.filter(bursary__receipt_date__gt = startdate)

        if enddate:
            querysetInvoices = querysetInvoices.filter(issueDate__lte = enddate)
            querysetReceipts = querysetReceipts.filter(transaction_date__lte = enddate)
            querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__lte = enddate)
            querysetBursaries = querysetBursaries.filter(bursary__receipt_date__lte = enddate)


        studentTransactionList = []

        for value in querysetReceipts:
            term_name = getattr(value.term, 'term_name', None)
            year_name = getattr(value.year, 'academic_year', None)
            student_class = getattr(value, 'student_class', None)
            transaction_date = getattr(value, 'transaction_date', None)
            description = f"{student_class}-{term_name}-{year_name}"

            item = StudentTransactionsPrintView(
                transactionDate=transaction_date,
                transactionType="FEE COLLECTION",
                description=description,
                expected="",
                paid=value.totalAmount
            )
            item.save()
            studentTransactionList.append(item)

        for value in querysetPIKReceipts:
            term_name = getattr(value.term, 'term_name', None)
            year_name = getattr(value.year, 'academic_year', None)
            student_class = getattr(value, 'student_class', None)
            transaction_date = getattr(value, 'receipt_date', None)
            description = f"{student_class}-{term_name}-{year_name}"

            item = StudentTransactionsPrintView(
                transactionDate=transaction_date,
                transactionType="PAYMENT IN KIND",
                description=description,
                expected="",
                paid=value.totalAmount
            )
            item.save()
            studentTransactionList.append(item)

        for value in querysetBursaries:
            term_name = getattr(value.bursary.term, 'term_name', None)
            year_name = getattr(value.bursary.year, 'academic_year', None)
            student_class = getattr(value, 'student_class', None)
            transaction_date = getattr(value.bursary, 'receipt_date', None)
            description = f"{student_class}-{term_name}-{year_name}"

            item = StudentTransactionsPrintView(
                transactionDate=transaction_date,
                transactionType="BURSARY",
                description=description,
                expected="",
                paid=value.amount
            )
            item.save()
            studentTransactionList.append(item)

        for value in querysetInvoices:
            term_name = getattr(value.term, 'term_name', None)
            year_name = getattr(value.year, 'academic_year', None)
            student_class = getattr(value, 'classes', None)
            transaction_date = getattr(value, 'issueDate', None)
            description = f"{student_class}-{term_name}-{year_name}"

            item = StudentTransactionsPrintView(
                transactionDate=transaction_date,
                transactionType="FEES INVOICE",
                description=description,
                expected=value.amount,
                paid=""
            )
            item.save()
            studentTransactionList.append(item)


        for value in studentTransactionList:
            print(f"{value} - {value.transactionType}")

        def get_transaction_date(item):
            transaction_date = getattr(item, 'transactionDate', date.max)
            if isinstance(transaction_date, str):
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()

            return transaction_date

        studentTransactionList = sorted(studentTransactionList, key=get_transaction_date)
        serializer = StudentTransactionsPrintViewSerializer(studentTransactionList, many=True)

        return Response({"detail": serializer.data})
