# Create your views here.
from datetime import date, datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from academic_year.models import AcademicYear
from appcollections.models import Collection
from invoices.models import Invoice
from items.models import Item
from payment_in_kind_Receipt.models import PIKReceipt
from payment_in_kinds.models import PaymentInKind
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from receipts.serializers import ReceiptSerializer
from reportss.models import ReportStudentBalance, StudentTransactionsPrintView, IncomeSummary, ReceivedCheque, \
    BalanceTracker
from reportss.serializers import ReportStudentBalanceSerializer, StudentTransactionsPrintViewSerializer, \
    IncomeSummarySerializer, ReceivedChequeSerializer
from students.models import Student
from students.serializers import StudentSerializer
from term.models import Term
from utils import SchoolIdMixin, currentAcademicYear, currentTerm, IsAdminOrSuperUser
from voteheads.models import VoteHead
from vouchers.models import Voucher


class ReportStudentBalanceView(APIView, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def calculate(self, queryset, startdate, enddate, boardingstatus, term, year):

        print(f"1")
        if boardingstatus:
            queryset.filter(boarding_status=boardingstatus)

        reportsStudentBalanceList = []

        current_academic_year = currentAcademicYear()
        current_term = currentTerm()

        try:
            if year:
                year = get_object_or_404(AcademicYear, id=year)
            else:
                year = current_academic_year
        except:
            return []

        try:
            if term:
                term = get_object_or_404(Term, id=term)
            else:
                term = current_term
        except:
            return []

        for student in queryset:
            totalExpected = Decimal('0.0')
            totalPaid = Decimal('0.0')

            invoiceList = Invoice.objects.filter(term=term, year=year, student=student)
            if startdate:
                invoiceList = invoiceList.filter(issueDate__gt=startdate, issueDate__isnull=False)
            if enddate:
                invoiceList = invoiceList.filter(issueDate__lte=enddate, issueDate__isnull=False)
            totalExpected += invoiceList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')

            receiptList = Receipt.objects.filter(term=term, year=year, student=student, is_reversed=False)
            if startdate:
                receiptList = receiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                receiptList = receiptList.filter(receipt_date__lte=enddate, receipt_date__isnull=False)
            paid = receiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            pikReceiptList = PIKReceipt.objects.filter(term=term, year=year, student=student, is_posted=True)
            if startdate:
                pikReceiptList = pikReceiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                pikReceiptList = pikReceiptList.filter(receipt_date__lte=enddate, receipt_dte__isnull=False)
            paid = pikReceiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            bursaryItemList = Item.objects.filter(bursary__term=term, bursary__year=year, student=student,bursary__posted=True)

            if startdate:
                bursaryItemList = bursaryItemList.filter(item_date__gt=startdate, item_date__isnull=False)
            if enddate:
                bursaryItemList = bursaryItemList.filter(item_date__lte=enddate, item_date__isnull=False)
            paid = bursaryItemList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            boarding_status = None

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

        try:
            queryset = Student.objects.filter(school_id=school_id)

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

            if not currentClass and not stream and not student:
                print("here")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if currentClass:
                queryset = queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if stream:
                # if not currentClass:
                # return Response({'detail': f"Both Class and Stream must be entered to query stream"},status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(current_Stream=stream)
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if student:
                queryset = queryset.filter(id=student)
                print(f"student was passed {queryset}")
                reportsStudentBalanceList = self.calculate(queryset, startdate, enddate, boardingstatus, term, year)

            if amountbelow:
                amountbelow = Decimal(amountbelow)
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance < amountbelow]

            if amountabove:
                amountabove = Decimal(amountabove)
                print(f"Amount above was passed {reportsStudentBalanceList}")
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance > amountabove]

            print(f"Students List is {reportsStudentBalanceList}")
            serializer = ReportStudentBalanceSerializer(reportsStudentBalanceList, many=True)
            serialized_data = serializer.data
            return Response({'detail': serialized_data}, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


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

        try:
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
                querysetInvoices = querysetInvoices.filter(issueDate__gt = startdate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__gt = startdate, transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__gt = startdate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__gt = startdate, bursary__receipt_date__isnull=False)

            if enddate:
                querysetInvoices = querysetInvoices.filter(issueDate__lte = enddate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__lte = enddate,  transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__lte = enddate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__lte = enddate, bursary__receipt_date__isnull=False)

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
                print(f"{value.transactionDate} - {value.transactionType}")

            def get_transaction_date(item):
                transaction_date = getattr(item, 'transactionDate', date.max)
                if isinstance(transaction_date, str):
                    transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()

                return transaction_date

            studentTransactionList = sorted(studentTransactionList, key=get_transaction_date)
            serializer = StudentTransactionsPrintViewSerializer(studentTransactionList, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})



class StudentCollectionListView(SchoolIdMixin, generics.RetrieveAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):

        try:
            student = self.get_object()

            print(f"Student is {student}")

            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')
            term = request.GET.get('term')
            academicYear = request.GET.get('academicYear')

            queryset = Receipt.objects.filter(
                student_id=student.id,
                school_id=school_id
            )

            if term:
                queryset = queryset.filter(term__id=term)

            if academicYear:
                queryset = queryset.filter(year__id=academicYear)

            if startdate:
                queryset = queryset.filter(transaction_date__gt = startdate, transaction_date__isnull=False)

            if enddate:
                queryset = queryset.filter(transaction_date__lte = enddate,transaction_date__isnull=False)

            serializer = ReceiptSerializer(queryset, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})


class IncomeSummaryView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):


        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            querysetCollections = Collection.objects.filter(
                school_id=school_id
            )

            querysetPIK = PaymentInKind.objects.filter(
                school_id=school_id
            )

            if not orderby or not accounttype:
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetCollections = querysetCollections.filter(receipt__account_type__id=accounttype)
            querysetPIK = querysetPIK.filter(receipt__bank_account__account_type__id = accounttype)

            if startdate:
                querysetCollections = querysetCollections.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
            if enddate:
                querysetCollections = querysetCollections.filter(transaction_date__lte=enddate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__lte=enddate, transaction_date__isnull=False)

            incomeSummaryList = []


            paymentMethods = PaymentMethod.objects.filter(school__id = school_id)

            if orderby == "paymentmode":
                for paymentmode in paymentMethods:
                    totalAmount = Decimal('0.0')
                    paymentmode_name = paymentmode.name

                    for collection in querysetCollections:
                        if collection.receipt.payment_method == paymentmode:
                            totalAmount += collection.amount

                    for pik in querysetPIK:
                        if pik.receipt.payment_method == paymentmode:
                            totalAmount += pik.amount

                    item = IncomeSummary(
                        votehead_name=paymentmode_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)


            voteheads = VoteHead.objects.all()
            if orderby == "votehead":
                for votehead in voteheads:
                    totalAmount = Decimal('0.0')
                    votehead_name = votehead.vote_head_name

                    for collection in querysetCollections:
                        if collection.votehead == votehead:
                            totalAmount += collection.amount

                    for pik in querysetPIK:
                        if pik.votehead == votehead:
                            totalAmount += pik.amount

                    item = IncomeSummary(
                        votehead_name=votehead_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)

            serializer = IncomeSummarySerializer(incomeSummaryList, many=True)

            grandTotal = Decimal('0.0')
            for income_summary in incomeSummaryList:
                print(f'Type of income_summary.amount: {type(income_summary.amount)}')
                print(f'Type of grandTotal before addition: {type(grandTotal)}')
                grandTotal += income_summary.amount

            thedata = {
                'summary': serializer.data,
                'grandtotal': grandTotal
            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})


class ExpenseSummaryView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            querysetExpenses = Voucher.objects.filter(
                school_id=school_id
            )

            if not orderby or not accounttype:
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetExpenses = querysetExpenses.filter(bank_account__account_type__id=accounttype)

            if startdate:
                querysetExpenses = querysetExpenses.filter(paymentDate__gt=startdate, paymentDate__isnull=False)
            if enddate:
                querysetExpenses = querysetExpenses.filter(paymentDate__lte=enddate, paymentDate__isnull=False)


            incomeSummaryList = []

            paymentMethods = PaymentMethod.objects.filter(school__id = school_id)

            if orderby == "paymentmode":
                for paymentmode in paymentMethods:
                    totalAmount = Decimal('0.0')
                    paymentmode_name = paymentmode.name

                    for voucher in querysetExpenses:
                        for expense in voucher.voucher_items.all():
                            if expense.voucher.payment_Method == paymentmode:
                                totalAmount += expense.amount

                    item = IncomeSummary(
                        votehead_name=paymentmode_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)


            voteheads = VoteHead.objects.all()
            if orderby == "votehead":
                for votehead in voteheads:
                    totalAmount = Decimal('0.0')
                    votehead_name = votehead.vote_head_name

                    for voucher in querysetExpenses:
                        for expense in voucher.voucher_items.all():
                            if expense.votehead == votehead:
                                totalAmount += expense.amount

                    item = IncomeSummary(
                        votehead_name=votehead_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)

            serializer = IncomeSummarySerializer(incomeSummaryList, many=True)

            grandTotal = Decimal('0.0')
            for expense_summary in incomeSummaryList:
                print(f'Type of expense_summary.amount: {type(expense_summary.amount)}')
                print(f'Type of grandTotal before addition: {type(grandTotal)}')
                grandTotal += expense_summary.amount

            thedata = {
                'summary': serializer.data,
                'grandtotal': grandTotal
            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})





class ReceivedChequesView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            paymentMethod = request.GET.get('paymentmethod')

            if not paymentMethod:
                return Response({'detail': f"Payment Method required"}, status=status.HTTP_400_BAD_REQUEST)

            querysetCollections = Collection.objects.filter(school_id=school_id, receipt__payment_method__id = paymentMethod )

            chequeCollectionList = []
            for collection in querysetCollections:
                creationdate = collection.receipt.dateofcreation
                transactiondate = collection.receipt.transaction_date
                chequeNo = collection.receipt.transaction_code
                student = collection.student
                currency = collection.receipt.currency
                amount = collection.amount

                item = ReceivedCheque(
                    transactionDate=transactiondate,
                    dateofcreation=creationdate,
                    chequeNo=chequeNo,
                    student=student,
                    currency=currency,
                    amount=amount
                )
                item.save()
                chequeCollectionList.append(item)

            serializer = ReceivedChequeSerializer(chequeCollectionList, many=True)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.data})









class CashBookView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            bankaccount = request.GET.get('bankaccount')
            accounttype = request.GET.get('accounttype')
            financialyear = request.GET.get('financialyear')
            month = request.GET.get('month')

            querySetReceipts = Receipt.objects.filter(school_id=school_id)
            querysetPIK = PIKReceipt.objects.filter(school_id=school_id)
            querySetExpenses = Voucher.objects.filter(school_id=school_id)

            if bankaccount:
                querySetReceipts = querySetReceipts.filter(school_id=school_id, bank_account__id = bankaccount)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__id = bankaccount)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, bank_account__id = bankaccount)

            if accounttype:
                querySetReceipts = querySetReceipts.filter(school_id=school_id, account_type__id=accounttype)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__account_type__id=accounttype)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, bank_account__account_type__id=accounttype)

            if financialyear:
                querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
                querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, financial_year__id=financialyear)

            if month:
                querySetReceipts = querySetReceipts.filter(school_id=school_id, dateofcreation__month=month)
                querysetPIK = querysetPIK.filter(school_id=school_id, dateofcreation__month=month)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, dateofcreation__month=month)

            # if not bankaccount or not accounttype:
            #     return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            listofdateofcreations = []
            listofdateofcreations.extend(querySetReceipts.values_list('dateofcreation', flat=True))
            listofdateofcreations.extend(querysetPIK.values_list('dateofcreation', flat=True))
            listofdateofcreations = list(set(listofdateofcreations))
            listofdateofcreations = list(listofdateofcreations)

            listofreceipts = []
            universalvoteheadDictionary = {}

            for dateinstance in listofdateofcreations:
                receipt_range = []
                total_amount = Decimal("0.0")
                cash = Decimal("0.0")
                bank = Decimal("0.0")
                inkind = Decimal("0.0")
                voteheadDictionary = {}
                for receipt in querySetReceipts:
                    if receipt.dateofcreation == dateinstance:
                        method = "NONE"
                        if receipt.payment_method:
                            method = "CASH" if receipt.payment_method.is_cash else "BANK" if receipt.payment_method.is_bank else "NONE"
                        if method == "CASH":
                            cash += Decimal(receipt.totalAmount)
                        if method == "BANK":
                            bank += Decimal(receipt.totalAmount)
                        if method == "NONE":
                            inkind += Decimal(receipt.totalAmount)

                        counter = receipt.counter
                        amount = Decimal(receipt.totalAmount)
                        receipt_range.append(counter)
                        total_amount += amount
                        if "total_amount" not in universalvoteheadDictionary:
                            universalvoteheadDictionary[f"total_amount"] = Decimal(amount)
                        else:
                            universalvoteheadDictionary[f"total_amount"] += Decimal(amount)

                    collections = Collection.objects.filter(receipt=receipt)
                    for collection in collections:
                        if collection.votehead.vote_head_name not in voteheadDictionary:
                            voteheadDictionary[f"{collection.votehead.vote_head_name}"] = Decimal(collection.amount)
                        else:
                            voteheadDictionary[f"{collection.votehead.vote_head_name}"] += Decimal(collection.amount)

                        if collection.votehead.vote_head_name not in universalvoteheadDictionary:
                            universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] = Decimal(collection.amount)
                        else:
                            universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] += Decimal(collection.amount)



                for pikreceipt in querysetPIK:
                    if pikreceipt.dateofcreation == dateinstance:
                        inkind += Decimal(pikreceipt.totalAmount)
                        counter = pikreceipt.counter
                        amount = Decimal(pikreceipt.totalAmount)
                        receipt_range.append(counter)
                        total_amount += amount

                    piks = PaymentInKind.objects.filter(receipt=pikreceipt)
                    for pik in piks:
                        if pik.votehead.vote_head_name not in voteheadDictionary:
                            voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                        else:
                            voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
                        if pik.votehead.vote_head_name not in universalvoteheadDictionary:
                            universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                        else:
                            universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount


                result = ""
                if receipt_range:
                    print(f"Receipt range is {receipt_range}")
                    result = f"{min(receipt_range)} - {max(receipt_range)}"

                print(f"Total amount for date {dateinstance}: {total_amount}")
                print(f"voteheadDictionary for date {dateinstance}: {voteheadDictionary}")

                listofreceipts.append(
                    {
                        "date" : dateinstance,
                        "description": "Income",
                        "receipt_range": result,
                        "cash": cash,
                        "bank": bank,
                        "inkind": inkind,
                        "total_amount": total_amount,
                        "voteheads": voteheadDictionary,
                        "summary": universalvoteheadDictionary,
                    }
                )

            #EXPENSES OR VOUCHERS
            listofVoucherDateCreations = []
            listofVoucherDateCreations.extend(querySetExpenses.values_list('dateofcreation', flat=True))
            listofVoucherDateCreations = list(set(listofVoucherDateCreations))
            listofVoucherDateCreations = list(listofVoucherDateCreations)

            listofVouchers = []
            universal = {}

            for dateinstance in listofVoucherDateCreations:
                receipt_range = []
                total_amount = Decimal("0.0")
                cash = Decimal("0.0")
                bank = Decimal("0.0")
                voteheadDictionary = {}
                for voucher in querySetExpenses:
                    if voucher.dateofcreation == dateinstance:
                        method = "CASH" if voucher.payment_Method.is_cash else "BANK" if voucher.payment_Method.is_bank else "NONE"
                        if method == "CASH":
                            cash += Decimal(voucher.totalAmount)
                        if method == "BANK":
                            bank += Decimal(voucher.totalAmount)

                        counter = voucher.counter
                        amount = Decimal(voucher.totalAmount)
                        receipt_range.append(counter)
                        total_amount += amount
                        if "total_amount" not in universal:
                            universal[f"total_amount"] = Decimal(amount)
                        else:
                            universal[f"total_amount"] += Decimal(amount)

                        if voucher.expenseCategory.name not in voteheadDictionary:
                            voteheadDictionary[f"{voucher.expenseCategory.name}"] = Decimal(voucher.totalAmount)
                        else:
                            voteheadDictionary[f"{voucher.expenseCategory.name}"] += Decimal(voucher.totalAmount)

                        if voucher.expenseCategory.name not in universal:
                            universal[f"{voucher.expenseCategory.name}"] = Decimal(voucher.totalAmount)
                        else:
                            universal[f"{voucher.expenseCategory.name}"] += Decimal(voucher.totalAmount)



                result = ""
                if receipt_range:
                    result = f"{min(receipt_range)} - {max(receipt_range)}"

                listofVouchers.append(
                    {
                        "date": dateinstance,
                        "description": "Expense",
                        "receipt_range": result,
                        "cash": cash,
                        "bank": bank,
                        "total_amount": total_amount,
                        "voteheads": voteheadDictionary,
                        "summary": universal
                    }
                )

            thedata = {
                "receipts" : listofreceipts,
                "payments": listofVouchers
            }
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})





class FeeRegisterView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            student = request.GET.get('student')
            financialyear = request.GET.get('financialyear')
            academicyear = request.GET.get('academicyear')
            classes = request.GET.get('classes')
            stream = request.GET.get('stream')

            if not student and not classes and not stream:
                return Response({'detail': f"Either of Student or Stream or Class should be passed"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                student = Student.objects.get(id=student)
            except ObjectDoesNotExist:
                return Response({'detail': f"Invalid Student"}, status=status.HTTP_400_BAD_REQUEST)

            student_List = []
            if student:
                student_List.append(student)

            if classes:
                class_students = Student.objects.filter(current_Class__id = classes)
                if class_students:
                    for value in class_students:
                        student_List.append(value)

            if stream:
                stream_students = Student.objects.filter(current_Stream__id=classes)
                if stream_students:
                    for value in stream_students:
                        student_List.append(value)

            student_final_output = []

            for student in student_List:
                student_name = f"{student.first_name} - {student.last_name}"
                student_admission = student.admission_number
                student_class = student.current_Class
                student_stream = student.current_Stream

                querySetReceipts = Receipt.objects.filter(school_id=school_id, student=student)
                querysetPIK = PIKReceipt.objects.filter(school_id=school_id, student=student)

                if financialyear:
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)

                if academicyear:
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, year__id = academicyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, year__id = academicyear)


                listofdateofcreations = []
                listofdateofcreations.extend(querySetReceipts.values_list('dateofcreation', flat=True))
                listofdateofcreations.extend(querysetPIK.values_list('dateofcreation', flat=True))
                listofdateofcreations = list(set(listofdateofcreations))
                listofdateofcreations = list(listofdateofcreations)

                listofreceipts = []
                universalvoteheadDictionary = {}


                dated_instances = []

                for dateinstance in listofdateofcreations:

                    receipts = []

                    for receipt in querySetReceipts:
                        voteheadDictionary = {}
                        if receipt.dateofcreation == dateinstance:
                            receipt_number = receipt.receipt_No
                            balance_before = "0.0"
                            amount_paid = "0.0"
                            balance_after = "0.0"

                            balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
                            if balanceTrackerQuerySet:
                                balance_before = balanceTrackerQuerySet.balanceBefore
                                balance_after = balanceTrackerQuerySet.balanceAfter
                                amount_paid = balanceTrackerQuerySet.amountPaid

                            receiptsList = Collection.objects.filter(receipt=receipt)
                            for collection in receiptsList:
                                if collection.votehead.vote_head_name not in voteheadDictionary:
                                    voteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
                                else:
                                    voteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount
                                if collection.votehead.vote_head_name not in universalvoteheadDictionary:
                                    universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
                                else:
                                    universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount

                            receiptObject = {
                                "date": dateinstance,
                                "receipt_number": receipt_number,
                                "balance_before": balance_before,
                                "balance_after": balance_after,
                                "transaction_amount": amount_paid,
                                "voteheads": voteheadDictionary,
                            }

                            receipts.append(receiptObject)

                    for pik in querysetPIK:
                        voteheadDictionary = {}
                        if pik.dateofcreation == dateinstance:
                            receipt_number = pik.receipt_No
                            balance_before = "0.0"
                            amount_paid = "0.0"
                            balance_after = "0.0"

                            balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
                            if balanceTrackerQuerySet:
                                balance_before = balanceTrackerQuerySet.balanceBefore
                                balance_after = balanceTrackerQuerySet.balanceAfter
                                amount_paid = balanceTrackerQuerySet.amountPaid

                            piks = PaymentInKind.objects.filter(receipt=pik)
                            for pik in piks:
                                if pik.votehead.vote_head_name not in voteheadDictionary:
                                    voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                                else:
                                    voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
                                if pik.votehead.vote_head_name not in universalvoteheadDictionary:
                                    universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                                else:
                                    universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount

                            receiptObject = {
                                "date": dateinstance,
                                "receipt_number": receipt_number,
                                "balance_before": balance_before,
                                "balance_after": balance_after,
                                "transaction_amount": amount_paid,
                                "voteheads": voteheadDictionary,
                            }
                            receipts.append(receiptObject)


                    output = {
                        "date": dateinstance,
                        "receipts": receipts,
                    }

                    dated_instances.append(output)


                student_final_output.append(
                    {
                        "dated_student_instances": dated_instances,
                        "student": StudentSerializer(student).data,
                        "totals": universalvoteheadDictionary
                    }
                )

            thedata = student_final_output

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})




# class TrialBalanceView(SchoolIdMixin, generics.GenericAPIView):
#     queryset = Student.objects.all()
#     serializer_class = StudentSerializer
#
#     def get(self, request, *args, **kwargs):
#         school_id = self.check_school_id(request)
#         if not school_id:
#             return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
#
#         try:
#             school_id = self.check_school_id(request)
#             if not school_id:
#                 return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
#
#             financialyear = request.GET.get('financialyear')
#             accounttype = request.GET.get('accounttype')
#             month = request.GET.get('month')
#
#             if not financialyear and not accounttype and not month:
#                 return Response({'detail': f"Account Type, Financial Year and Month are required"}, status=status.HTTP_400_BAD_REQUEST)
#
#
#
#
#
#
#
#
#
#
#
#
#             try:
#                 student = Student.objects.get(id=student)
#             except ObjectDoesNotExist:
#                 return Response({'detail': f"Invalid Student"}, status=status.HTTP_400_BAD_REQUEST)
#
#             student_List = []
#             if student:
#                 student_List.append(student)
#
#             if classes:
#                 class_students = Student.objects.filter(current_Class__id = classes)
#                 if class_students:
#                     for value in class_students:
#                         student_List.append(value)
#
#             if stream:
#                 stream_students = Student.objects.filter(current_Stream__id=classes)
#                 if stream_students:
#                     for value in stream_students:
#                         student_List.append(value)
#
#             student_final_output = []
#
#             for student in student_List:
#                 student_name = f"{student.first_name} - {student.last_name}"
#                 student_admission = student.admission_number
#                 student_class = student.current_Class
#                 student_stream = student.current_Stream
#
#                 querySetReceipts = Receipt.objects.filter(school_id=school_id, student=student)
#                 querysetPIK = PIKReceipt.objects.filter(school_id=school_id, student=student)
#
#                 if financialyear:
#                     querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
#                     querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)
#
#                 if academicyear:
#                     querySetReceipts = querySetReceipts.filter(school_id=school_id, year__id = academicyear)
#                     querysetPIK = querysetPIK.filter(school_id=school_id, year__id = academicyear)
#
#
#                 listofdateofcreations = []
#                 listofdateofcreations.extend(querySetReceipts.values_list('dateofcreation', flat=True))
#                 listofdateofcreations.extend(querysetPIK.values_list('dateofcreation', flat=True))
#                 listofdateofcreations = list(set(listofdateofcreations))
#                 listofdateofcreations = list(listofdateofcreations)
#
#                 listofreceipts = []
#                 universalvoteheadDictionary = {}
#
#
#                 dated_instances = []
#
#                 for dateinstance in listofdateofcreations:
#
#                     receipts = []
#
#                     for receipt in querySetReceipts:
#                         voteheadDictionary = {}
#                         if receipt.dateofcreation == dateinstance:
#                             receipt_number = receipt.receipt_No
#                             balance_before = "0.0"
#                             amount_paid = "0.0"
#                             balance_after = "0.0"
#
#                             balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
#                             if balanceTrackerQuerySet:
#                                 balance_before = balanceTrackerQuerySet.balanceBefore
#                                 balance_after = balanceTrackerQuerySet.balanceAfter
#                                 amount_paid = balanceTrackerQuerySet.amountPaid
#
#                             receiptsList = Collection.objects.filter(receipt=receipt)
#                             for collection in receiptsList:
#                                 if collection.votehead.vote_head_name not in voteheadDictionary:
#                                     voteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
#                                 else:
#                                     voteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount
#                                 if collection.votehead.vote_head_name not in universalvoteheadDictionary:
#                                     universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
#                                 else:
#                                     universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] += collection.amount
#
#                             receiptObject = {
#                                 "date": dateinstance,
#                                 "receipt_number": receipt_number,
#                                 "balance_before": balance_before,
#                                 "balance_after": balance_after,
#                                 "transaction_amount": amount_paid,
#                                 "voteheads": voteheadDictionary,
#                             }
#
#                             receipts.append(receiptObject)
#
#                     for pik in querysetPIK:
#                         voteheadDictionary = {}
#                         if pik.dateofcreation == dateinstance:
#                             receipt_number = pik.receipt_No
#                             balance_before = "0.0"
#                             amount_paid = "0.0"
#                             balance_after = "0.0"
#
#                             balanceTrackerQuerySet = BalanceTracker.objects.filter(dateofcreation=dateinstance, school_id = school_id, student = student).first()
#                             if balanceTrackerQuerySet:
#                                 balance_before = balanceTrackerQuerySet.balanceBefore
#                                 balance_after = balanceTrackerQuerySet.balanceAfter
#                                 amount_paid = balanceTrackerQuerySet.amountPaid
#
#                             piks = PaymentInKind.objects.filter(receipt=pik)
#                             for pik in piks:
#                                 if pik.votehead.vote_head_name not in voteheadDictionary:
#                                     voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
#                                 else:
#                                     voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
#                                 if pik.votehead.vote_head_name not in universalvoteheadDictionary:
#                                     universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
#                                 else:
#                                     universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
#
#                             receiptObject = {
#                                 "date": dateinstance,
#                                 "receipt_number": receipt_number,
#                                 "balance_before": balance_before,
#                                 "balance_after": balance_after,
#                                 "transaction_amount": amount_paid,
#                                 "voteheads": voteheadDictionary,
#                             }
#                             receipts.append(receiptObject)
#
#
#                     output = {
#                         "date": dateinstance,
#                         "receipts": receipts,
#                     }
#
#                     dated_instances.append(output)
#
#
#                 student_final_output.append(
#                     {
#                         "dated_student_instances": dated_instances,
#                         "student": StudentSerializer(student).data,
#                         "totals": universalvoteheadDictionary
#                     }
#                 )
#
#             thedata = student_final_output
#
#         except Exception as exception:
#             return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
#
#         return Response({"detail": thedata})




#
#
# def getOpeningBalance(accounttype, month, financialyear, school_id):
#
#     try:
#         querySetReceipts = Receipt.objects.filter(school_id=school_id)
#         querysetPIK = PIKReceipt.objects.filter(school_id=school_id)
#
#         if accounttype:
#             querySetReceipts = querySetReceipts.filter(school_id=school_id, account_type__id=accounttype)
#             querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__account_type__id=accounttype)
#
#         if financialyear:
#             querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
#             querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)
#
#         if month:
#             querySetReceipts = querySetReceipts.filter(school_id=school_id, dateofcreation__month=month)
#             querysetPIK = querysetPIK.filter(school_id=school_id, dateofcreation__month=month)
#
#
#         listofdateofcreations = []
#         listofdateofcreations.extend(querySetReceipts.values_list('dateofcreation', flat=True))
#         listofdateofcreations.extend(querysetPIK.values_list('dateofcreation', flat=True))
#         listofdateofcreations = list(set(listofdateofcreations))
#         listofdateofcreations = list(listofdateofcreations)
#
#         listofreceipts = []
#         universalvoteheadDictionary = {}
#
#         for dateinstance in listofdateofcreations:
#             receipt_range = []
#             total_amount = Decimal("0.0")
#             cash = Decimal("0.0")
#             bank = Decimal("0.0")
#             inkind = Decimal("0.0")
#             voteheadDictionary = {}
#             for receipt in querySetReceipts:
#                 if receipt.dateofcreation == dateinstance:
#                     method = "NONE"
#                     if receipt.payment_method:
#                         method = "CASH" if receipt.payment_method.is_cash else "BANK" if receipt.payment_method.is_bank else "NONE"
#                     if method == "CASH":
#                         cash += Decimal(receipt.totalAmount)
#                     if method == "BANK":
#                         bank += Decimal(receipt.totalAmount)
#                     if method == "NONE":
#                         inkind += Decimal(receipt.totalAmount)
#
#                     counter = receipt.counter
#                     amount = Decimal(receipt.totalAmount)
#                     receipt_range.append(counter)
#                     total_amount += amount
#                     if "total_amount" not in universalvoteheadDictionary:
#                         universalvoteheadDictionary[f"total_amount"] = Decimal(amount)
#                     else:
#                         universalvoteheadDictionary[f"total_amount"] += Decimal(amount)
#
#                 collections = Collection.objects.filter(receipt=receipt)
#                 for collection in collections:
#                     if collection.votehead.vote_head_name not in voteheadDictionary:
#                         voteheadDictionary[f"{collection.votehead.vote_head_name}"] = Decimal(collection.amount)
#                     else:
#                         voteheadDictionary[f"{collection.votehead.vote_head_name}"] += Decimal(collection.amount)
#
#                     if collection.votehead.vote_head_name not in universalvoteheadDictionary:
#                         universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] = Decimal(
#                             collection.amount)
#                     else:
#                         universalvoteheadDictionary[f"{collection.votehead.vote_head_name}"] += Decimal(
#                             collection.amount)
#
#             for pikreceipt in querysetPIK:
#                 if pikreceipt.dateofcreation == dateinstance:
#                     inkind += Decimal(pikreceipt.totalAmount)
#                     counter = pikreceipt.counter
#                     amount = Decimal(pikreceipt.totalAmount)
#                     receipt_range.append(counter)
#                     total_amount += amount
#
#                 piks = PaymentInKind.objects.filter(receipt=pikreceipt)
#                 for pik in piks:
#                     if pik.votehead.vote_head_name not in voteheadDictionary:
#                         voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
#                     else:
#                         voteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
#                     if pik.votehead.vote_head_name not in universalvoteheadDictionary:
#                         universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
#                     else:
#                         universalvoteheadDictionary[f"{pik.votehead.vote_head_name}"] += pik.amount
#
#             result = ""
#             if receipt_range:
#                 print(f"Receipt range is {receipt_range}")
#                 result = f"{min(receipt_range)} - {max(receipt_range)}"
#
#             print(f"Total amount for date {dateinstance}: {total_amount}")
#             print(f"voteheadDictionary for date {dateinstance}: {voteheadDictionary}")
#
#             listofreceipts.append(
#                 {
#                     "date": dateinstance,
#                     "description": "Income",
#                     "receipt_range": result,
#                     "cash": cash,
#                     "bank": bank,
#                     "inkind": inkind,
#                     "total_amount": total_amount,
#                     "voteheads": voteheadDictionary,
#                     "summary": universalvoteheadDictionary,
#                 }
#             )
#
#         # EXPENSES OR VOUCHERS
#         listofVoucherDateCreations = []
#         listofVoucherDateCreations.extend(querySetExpenses.values_list('dateofcreation', flat=True))
#         listofVoucherDateCreations = list(set(listofVoucherDateCreations))
#         listofVoucherDateCreations = list(listofVoucherDateCreations)
#
#         listofVouchers = []
#         universal = {}
#
#         for dateinstance in listofVoucherDateCreations:
#             receipt_range = []
#             total_amount = Decimal("0.0")
#             cash = Decimal("0.0")
#             bank = Decimal("0.0")
#             voteheadDictionary = {}
#             for voucher in querySetExpenses:
#                 if voucher.dateofcreation == dateinstance:
#                     method = "CASH" if voucher.payment_Method.is_cash else "BANK" if voucher.payment_Method.is_bank else "NONE"
#                     if method == "CASH":
#                         cash += Decimal(voucher.totalAmount)
#                     if method == "BANK":
#                         bank += Decimal(voucher.totalAmount)
#
#                     counter = voucher.counter
#                     amount = Decimal(voucher.totalAmount)
#                     receipt_range.append(counter)
#                     total_amount += amount
#                     if "total_amount" not in universal:
#                         universal[f"total_amount"] = Decimal(amount)
#                     else:
#                         universal[f"total_amount"] += Decimal(amount)
#
#                     if voucher.expenseCategory.name not in voteheadDictionary:
#                         voteheadDictionary[f"{voucher.expenseCategory.name}"] = Decimal(voucher.totalAmount)
#                     else:
#                         voteheadDictionary[f"{voucher.expenseCategory.name}"] += Decimal(voucher.totalAmount)
#
#                     if voucher.expenseCategory.name not in universal:
#                         universal[f"{voucher.expenseCategory.name}"] = Decimal(voucher.totalAmount)
#                     else:
#                         universal[f"{voucher.expenseCategory.name}"] += Decimal(voucher.totalAmount)
#
#             result = ""
#             if receipt_range:
#                 result = f"{min(receipt_range)} - {max(receipt_range)}"
#
#             listofVouchers.append(
#                 {
#                     "date": dateinstance,
#                     "description": "Expense",
#                     "receipt_range": result,
#                     "cash": cash,
#                     "bank": bank,
#                     "total_amount": total_amount,
#                     "voteheads": voteheadDictionary,
#                     "summary": universal
#                 }
#             )
#
#         thedata = {
#             "receipts": listofreceipts,
#             "payments": listofVouchers
#         }
#     except Exception as exception:
#         return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
#
#     return Response({"detail": thedata})

