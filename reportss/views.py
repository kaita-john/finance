# Create your views here.
from _decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from invoices.models import Invoice
from items.models import Item
from payment_in_kind_Receipt.models import PIKReceipt
from receipts.models import Receipt
from reportss.models import ReportStudentBalance
from reportss.serializers import ReportStudentBalanceSerializer
from students.models import Student
from utils import SchoolIdMixin, currentAcademicYear, currentTerm, IsAdminOrSuperUser

class ReportStudentBalanceView(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def calculate(self, queryset, startdate, enddate, boardingstatus):

        if boardingstatus:
            queryset.filter(boarding_status=boardingstatus)

        reportsStudentBalanceList = []

        currentSchoolYear = currentAcademicYear()
        currentSchoolTerm = currentTerm()
        if not currentSchoolYear:
            Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
        if not currentSchoolTerm:
            Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

        for student in queryset:
            totalExpected = Decimal('0.0')
            totalPaid = Decimal('0.0')

            invoiceList = Invoice.objects.filter(term=currentSchoolTerm, year=currentSchoolYear, student=student)
            if startdate:
                 invoiceList = invoiceList.filter(issueDate__gt=startdate)
            if enddate:
                invoiceList = invoiceList.filter(issueDate__lte=enddate)
            totalExpected += invoiceList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')


            receiptList = Receipt.objects.filter(term=currentSchoolTerm, year=currentSchoolYear, student=student,is_reversed=False)
            if startdate:
                 receiptList = receiptList.filter(receipt_date__gt=startdate)
            if enddate:
                receiptList = receiptList.filter(receipt_date__lte=enddate)
            paid = receiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid


            pikReceiptList = PIKReceipt.objects.filter(term=currentSchoolTerm, year=currentSchoolYear, student=student,is_posted=True)
            if startdate:
                 pikReceiptList = pikReceiptList.filter(receipt_date__gt=startdate)
            if enddate:
                pikReceiptList = pikReceiptList.filter(receipt_date__lte=enddate)
            paid = pikReceiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            bursaryItemList = Item.objects.filter(bursary__term=currentSchoolTerm, bursary__year=currentSchoolYear,student=student, bursary__posted=True)
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

        reportsStudentBalanceList = []

        try:
            if not currentClass and not stream and not student:
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus)
                print(f"None was passed reportsStudentBalanceList {reportsStudentBalanceList}")

            if currentClass:
                queryset = queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus)

            if stream:
                if not currentClass:
                    return Response({'detail': f"Both Class and Stream must be entered to query stream"}, status=status.HTTP_400_BAD_REQUEST)
                queryset =  queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus)

            if student:
                queryset = queryset.filter(id=student)
                print(f"student was passed {queryset}")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate,  boardingstatus)

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
