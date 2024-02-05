# Create your views here.
from collections import defaultdict
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
from account_types.models import AccountType
from appcollections.models import Collection
from bank_accounts.models import BankAccount
from budgets.models import Budget
from bursaries.models import Bursary
from currencies.serializers import CurrencySerializer
from financial_years.models import FinancialYear
from grant_items.models import GrantItem
from grants.models import Grant
from invoices.models import Invoice
from items.models import Item
from payment_in_kind_Receipt.models import PIKReceipt
from payment_in_kinds.models import PaymentInKind
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from receipts.serializers import ReceiptSerializer
from reportss.models import ReportStudentBalance, StudentTransactionsPrintView, IncomeSummary, BalanceTracker, \
    OpeningClosingBalances
from reportss.serializers import ReportStudentBalanceSerializer, StudentTransactionsPrintViewSerializer, \
    IncomeSummarySerializer
from reportss.utils import getBalance, getBalancesByAccount, getBalancesByFinancialYear
from students.models import Student
from students.serializers import StudentSerializer
from term.models import Term
from utils import SchoolIdMixin, currentAcademicYear, currentTerm, IsAdminOrSuperUser, check_if_object_exists, \
    DefaultMixin
from voteheads.models import VoteHead
from voteheads.serializers import VoteHeadSerializer
from voucher_items.models import VoucherItem
from vouchers.models import Voucher


class ReportStudentBalanceView(APIView, DefaultMixin, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def calculate(self, school_id, queryset, startdate, enddate, boardingstatus, term, year):

        print(f"1")
        if boardingstatus:
            queryset.filter(boarding_status=boardingstatus)

        reportsStudentBalanceList = []

        current_academic_year = currentAcademicYear(school_id)
        current_term = currentTerm(school_id)

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

            invoiceList = Invoice.objects.filter(term=term, year=year, student=student, school_id = school_id)
            if startdate:
                invoiceList = invoiceList.filter(issueDate__gt=startdate, issueDate__isnull=False)
            if enddate:
                invoiceList = invoiceList.filter(issueDate__lte=enddate, issueDate__isnull=False)
            totalExpected += invoiceList.aggregate(result=Sum('amount')).get('result', Decimal('0.0')) or Decimal('0.0')

            receiptList = Receipt.objects.filter(term=term, year=year, school_id=school_id, student=student, is_reversed=False)
            if startdate:
                receiptList = receiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                receiptList = receiptList.filter(receipt_date__lte=enddate, receipt_date__isnull=False)
            paid = receiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            pikReceiptList = PIKReceipt.objects.filter(term=term, year=year, school_id=school_id, student=student, is_posted=True)
            if startdate:
                pikReceiptList = pikReceiptList.filter(receipt_date__gt=startdate, receipt_date__isnull=False)
            if enddate:
                pikReceiptList = pikReceiptList.filter(receipt_date__lte=enddate, receipt_dte__isnull=False)
            paid = pikReceiptList.aggregate(result=Sum('totalAmount')).get('result', Decimal('0.0')) or Decimal('0.0')
            totalPaid += paid

            bursaryItemList = Item.objects.filter(bursary__term=term, bursary__year=year, student=student,bursary__posted=True, school_id=school_id)

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
        self.check_defaults(self.request, school_id)

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
                reportsStudentBalanceList = self.calculate(school_id, queryset, startdate, enddate, boardingstatus, term, year)

            if currentClass and currentClass != "" and currentClass != "null":
                queryset = queryset.filter(current_Class=currentClass)
                reportsStudentBalanceList = self.calculate(school_id, queryset, startdate, enddate, boardingstatus, term, year)

            if stream and stream != "" and stream != "null":
                # if not currentClass:
                # return Response({'detail': f"Both Class and Stream must be entered to query stream"},status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(current_Stream=stream)
                reportsStudentBalanceList = self.calculate(school_id, queryset, startdate, enddate, boardingstatus, term, year)

            if student and student != "" and student != "null":
                queryset = queryset.filter(id=student)
                print(f"student was passed {queryset}")
                reportsStudentBalanceList = self.calculate(school_id, queryset, startdate, enddate, boardingstatus, term, year)

            if amountbelow and amountbelow != "" and amountbelow != "null":
                amountbelow = Decimal(amountbelow)
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance < amountbelow]

            if amountabove and amountabove != "" and amountabove != "null":
                amountabove = Decimal(amountabove)
                print(f"Amount above was passed {reportsStudentBalanceList}")
                reportsStudentBalanceList = [report for report in reportsStudentBalanceList if report.totalBalance > amountabove]

            print(f"Students List is {reportsStudentBalanceList}")
            serializer = ReportStudentBalanceSerializer(reportsStudentBalanceList, many=True)
            serialized_data = serializer.data
            return Response({'detail': serialized_data}, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)


class FilterStudents(APIView, DefaultMixin, SchoolIdMixin):
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    model = Student

    def get(self, request):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        currentClass = request.GET.get('currentClass')
        currentStream = request.GET.get('currentStream')
        admissionNumber = request.GET.get('admissionNumber')
        studentid = request.GET.get('studentid')

        queryset = Student.objects.filter(school_id=school_id)

        try:

            if not currentClass or not currentStream or not admissionNumber:
                pass

            if studentid and studentid != "" and studentid  != "null":
                queryset = queryset.filter(id = studentid)

            if admissionNumber and admissionNumber != "" and admissionNumber != "null":
                queryset = queryset.filter(admission_number = admissionNumber)

            if currentClass and currentClass != "" and currentClass != "null":
                queryset = queryset.filter(current_Class = currentClass)

            if currentStream and currentStream != "" and currentStream != "null":
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


class StudentTransactionsPrint(SchoolIdMixin, DefaultMixin, generics.RetrieveAPIView):
    queryset = Student.objects.filter()
    serializer_class = StudentSerializer
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):

        try:
            student = self.get_object()

            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
            self.check_defaults(self.request, school_id)

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
                school_id=school_id,
                is_reversed=False,
            )

            querysetPIKReceipts = PIKReceipt.objects.filter(
                is_posted=True,
                student_id=student.id,
                school_id=school_id
            )

            querysetBursaries = Item.objects.filter(
                student_id=student.id,
                school_id=school_id
            )

            if term and term != "" and term != "null":
                querysetInvoices = querysetInvoices.filter(term__id=term)
                querysetReceipts = querysetReceipts.filter(term__id=term)
                querysetPIKReceipts = querysetPIKReceipts.filter(term__id=term)
                querysetBursaries = querysetBursaries.filter(bursary__term__id=term)

            if academicYear and academicYear != "" and academicYear != "null":
                querysetInvoices = querysetInvoices.filter(year__id=academicYear)
                querysetReceipts = querysetReceipts.filter(year__id=academicYear)
                querysetPIKReceipts = querysetPIKReceipts.filter(year__id=academicYear)
                querysetBursaries = querysetBursaries.filter(bursary__year__id=academicYear)

            if startdate and startdate != "" and startdate != "null":
                querysetInvoices = querysetInvoices.filter(issueDate__gt = startdate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__gt = startdate, transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__gt = startdate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__gt = startdate, bursary__receipt_date__isnull=False)

            if enddate and enddate != "" and enddate != "null":
                querysetInvoices = querysetInvoices.filter(issueDate__lte = enddate, issueDate__isnull=False)
                querysetReceipts = querysetReceipts.filter(transaction_date__lte = enddate,  transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__lte = enddate, receipt_date__isnull=False)
                querysetBursaries = querysetBursaries.filter(bursary__receipt_date__lte = enddate, bursary__receipt_date__isnull=False)

            studentTransactionList = []

            for value in querysetReceipts:
                term_name = getattr(value.term, 'term_name', None)
                year_name = getattr(value.year, 'academic_year', None)
                student_class = getattr(value, 'student_class', None)
                transaction_date = getattr(value, 'dateofcreation', None)
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
                transaction_date = getattr(value, 'dateofcreation', None)
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
                transaction_date = getattr(value.bursary, 'dateofcreation', None)
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
                transaction_date = getattr(value, 'dateofcreation', None)
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



class StudentCollectionListView(SchoolIdMixin, DefaultMixin, generics.RetrieveAPIView):
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
            self.check_defaults(self.request, school_id)

            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')
            term = request.GET.get('term')
            academicYear = request.GET.get('academicYear')

            queryset = Receipt.objects.filter(
                is_reversed = False,
                student_id=student.id,
                school_id=school_id
            )

            querysetPIKReceipts = PIKReceipt.objects.filter(
                is_posted=True,
                student_id=student.id,
                school_id=school_id
            )

            if term and term != "" and term != "null":
                queryset = queryset.filter(term__id=term)
                querysetPIKReceipts = querysetPIKReceipts.filter(term__id=term)

            if academicYear and academicYear != "" and academicYear != "null":
                queryset = queryset.filter(year__id=academicYear)
                querysetPIKReceipts = querysetPIKReceipts.filter(year__id=academicYear)

            if startdate and startdate != "" and startdate != "null":
                queryset = queryset.filter(transaction_date__gt = startdate, transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__gt = startdate, receipt_date__isnull=False)

            if enddate and enddate != "" and enddate != "null":
                queryset = queryset.filter(transaction_date__lte = enddate,transaction_date__isnull=False)
                querysetPIKReceipts = querysetPIKReceipts.filter(receipt_date__lte = enddate,receipt_date__isnull=False)


            data = []

            for pik_receipt in querysetPIKReceipts:
                receipt_Date = pik_receipt.receipt_date
                creation_Date = pik_receipt.dateofcreation
                mode_of_payment = "PIK"
                receipt_no = pik_receipt.receipt_No
                transaction_code = "N|A"
                amount = pik_receipt.totalAmount
                receipt_id = pik_receipt.id

                data.append({
                    "receipt_Date": receipt_Date,
                    "creation_Date": creation_Date,
                    "mode_of_payment": mode_of_payment,
                    "receipt_no": receipt_no,
                    "transaction_code": transaction_code,
                    "amount": amount,
                    "receipt_id": receipt_id
                })


            for receipt in queryset:

                payment_method_name = getattr(receipt.payment_method, 'name', None)
                if receipt.payment_method:
                    payment_method_name = receipt.payment_method.name
                else:
                    payment_method_name = None

                receipt_Date = receipt.receipt_date
                creation_Date = receipt.dateofcreation
                mode_of_payment = payment_method_name
                receipt_no = receipt.receipt_No
                transaction_code = receipt.transaction_code
                amount = receipt.totalAmount
                receipt_id = receipt.id



                data.append({
                    "receipt_Date": receipt_Date,
                    "creation_Date": creation_Date,
                    "mode_of_payment": mode_of_payment,
                    "receipt_no": receipt_no,
                    "transaction_code": transaction_code,
                    "amount": amount,
                    "receipt_id": receipt_id
                })


        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": data})


class IncomeSummaryView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):


        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
            self.check_defaults(self.request, school_id)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            try:
                AccountType.objects.get(id=accounttype)
            except ObjectDoesNotExist:
                return Response({'detail': f"Invalid Account Type Id"}, status=status.HTTP_400_BAD_REQUEST)

            querysetGrants = GrantItem.objects.filter(
                grant__deleted = False,
                school_id=school_id
            )

            querysetCollections = Collection.objects.filter(
                receipt__is_reversed = False,
                school_id=school_id
            )

            querysetPIK = PaymentInKind.objects.filter(
                receipt__is_posted = True,
                school_id=school_id
            )

            if not orderby or orderby == "" or orderby == "null" or not accounttype or accounttype == "null" or accounttype == "":
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetCollections = querysetCollections.filter(receipt__account_type =accounttype)
            querysetPIK = querysetPIK.filter(receipt__bank_account__account_type  = accounttype)
            querysetGrants = querysetGrants.filter(grant__bankAccount__account_type = accounttype)

            if startdate and startdate != "" and startdate != "null":
                querysetCollections = querysetCollections.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__gt=startdate, transaction_date__isnull=False)
                querysetGrants = querysetGrants.filter(grant__receipt_date__gt=startdate, grant__receipt_date__isnull=False)
            if enddate and enddate != "" and enddate != "null":
                querysetCollections = querysetCollections.filter(transaction_date__lte=enddate, transaction_date__isnull=False)
                querysetPIK = querysetPIK.filter(transaction_date__lte=enddate, transaction_date__isnull=False)
                querysetGrants = querysetGrants.filter(grant__receipt_date__gt=enddate, grant__receipt_date__isnull=False)

            incomeSummaryList = []


            paymentMethods = PaymentMethod.objects.all()

            if orderby == "paymentmode":
                for paymentmode in paymentMethods:
                    totalAmount = Decimal('0.0')
                    paymentmode_name = paymentmode.name

                    for collection in querysetCollections:
                        if collection.receipt.payment_method == paymentmode:
                            totalAmount += collection.amount

                    if paymentmode.is_cash:
                        for pik in querysetPIK:
                            totalAmount += pik.amount

                    for grantitem in querysetGrants:
                        if grantitem.grant.paymentMethod == paymentmode:
                            totalAmount += grantitem.amount

                    item = IncomeSummary(
                        votehead_name=paymentmode_name,
                        amount=totalAmount
                    )
                    item.save()
                    incomeSummaryList.append(item)

            voteheads = VoteHead.objects.filter(school_id=school_id, account_type = accounttype)

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

                    for grantItem in querysetGrants:
                        if grantItem.votehead == votehead:
                            totalAmount += grantItem.amount

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


class ExpenseSummaryView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
            self.check_defaults(self.request, school_id)

            orderby = request.GET.get('orderby')
            accounttype = request.GET.get('accounttype')
            startdate = request.GET.get('startdate')
            enddate = request.GET.get('enddate')

            querysetExpenses = Voucher.objects.filter(
                is_deleted=False,
                school_id=school_id
            )

            if not AccountType.objects.filter(id=accounttype, school=school_id).exists():
                return Response({'detail': f"Invalid Account Type Id"}, status=status.HTTP_400_BAD_REQUEST)

            if not orderby or orderby == "" or orderby == "null" or not accounttype or accounttype == "" or accounttype == "null":
                return Response({'detail': f"Both orderby and accounttype values must be selected"}, status=status.HTTP_400_BAD_REQUEST)

            querysetExpenses = querysetExpenses.filter(bank_account__account_type__id=accounttype)

            if startdate and startdate != "" and startdate != "null":
                querysetExpenses = querysetExpenses.filter(paymentDate__gt=startdate, paymentDate__isnull=False)
            if enddate and enddate != "" and enddate != "null":
                querysetExpenses = querysetExpenses.filter(paymentDate__lte=enddate, paymentDate__isnull=False)


            incomeSummaryList = []

            paymentMethods = PaymentMethod.objects.all()

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


            voteheads = VoteHead.objects.filter(school_id=school_id, account_type = accounttype)
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





class ReceivedChequesView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
            self.check_defaults(self.request, school_id)

            querysetCollections = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                receipt__payment_method__is_cheque=True
            )

            querysetGrants = Grant.objects.filter(
                deleted=False,
                school_id=school_id
            )

            chequeCollectionList = []


            for grant in querysetGrants:
                creationdate = grant.dateofcreation
                transactiondate = grant.receipt_date
                chequeNo = grant.transactionNumber
                currency_data = CurrencySerializer(grant.currency).data if grant.currency else None
                student = None
                amount = grant.overall_amount

                chequeCollectionList.append({
                    "transactionDate": transactiondate,
                    "dateofcreation": creationdate,
                    "chequeNo": chequeNo,
                    "student": student,
                    "currency": currency_data,
                    "amount": amount
                })

            for collection in querysetCollections:
                creationdate = collection.receipt.dateofcreation
                transactiondate = collection.receipt.transaction_date
                chequeNo = collection.receipt.transaction_code
                student = collection.student

                currency_data = CurrencySerializer(collection.receipt.currency).data if collection.receipt.currency else None
                amount = collection.amount
                student_data = StudentSerializer(student).data if student else None

                chequeCollectionList.append({
                    "transactionDate": transactiondate,
                    "dateofcreation": creationdate,
                    "chequeNo": chequeNo,
                    "student": student_data,
                    "currency": currency_data,
                    "amount": amount
                })


        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": chequeCollectionList})









class CashBookView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            bankaccount = request.GET.get('bankaccount')
            accounttype = request.GET.get('accounttype')
            financialyear = request.GET.get('financialyear')
            month = request.GET.get('month')

            querySetReceipts = Receipt.objects.filter(school_id=school_id, is_reversed = False)
            querysetPIK = PIKReceipt.objects.filter(school_id=school_id, is_posted=True)
            querySetGrants = Grant.objects.filter(school_id=school_id, deleted = False)
            querySetExpenses = VoucherItem.objects.filter(school_id=school_id, voucher__is_deleted=False)
            querySetBursary = Bursary.objects.filter(school_id=school_id, posted=True)


            if bankaccount and bankaccount != "" and bankaccount != "null":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, bank_account=bankaccount)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account=bankaccount)
                querySetGrants = querySetGrants.filter(school_id=school_id, bankAccount=bankaccount)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__bank_account=bankaccount)
                querySetBursary = querySetBursary.filter(school_id=school_id, bankAccount=bankaccount)

            if accounttype and accounttype != "" and accounttype != "null":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, account_type=accounttype)
                querysetPIK = querysetPIK.filter(school_id=school_id, bank_account__account_type=accounttype)
                querySetGrants = querySetGrants.filter(school_id=school_id, bankAccount__account_type=accounttype)
                querySetExpenses = querySetExpenses.filter(school_id=school_id,voucher__bank_account__account_type=accounttype)
                querySetBursary = querySetBursary.filter(school_id=school_id, bankAccount__account_type=bankaccount)
            else:
                return Response({'detail': f"Account Type is required"}, status=status.HTTP_400_BAD_REQUEST)

            if financialyear and financialyear != "" and financialyear != "null":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year=financialyear)
                querysetPIK = querysetPIK.filter(school_id=school_id, financial_year=financialyear)
                querySetGrants = querySetGrants.filter(school_id=school_id, financial_year=financialyear)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__financial_year=financialyear)
                querySetBursary = querySetBursary.filter(school_id=school_id, financial_year=financialyear)

            if month and month != "" and month != "null":
                querySetReceipts = querySetReceipts.filter(school_id=school_id, transaction_date__month=month)
                querysetPIK = querysetPIK.filter(school_id=school_id, receipt_date__month=month)
                querySetExpenses = querySetExpenses.filter(school_id=school_id, voucher__paymentDate__month=month)
                querySetGrants = querySetGrants.filter(school_id=school_id, receipt_date__month=month)
                querySetBursary = querySetBursary.filter(school_id=school_id, receipt_date__month=month)



            listofdateofcreations = sorted(set(
                    querySetReceipts.values_list('transaction_date', flat=True).distinct() |
                    querysetPIK.values_list('receipt_date', flat=True).distinct() |
                    querySetGrants.values_list('receipt_date', flat=True).distinct() |
                    querySetBursary.values_list('bursary__receipt_date', flat=True).distinct()
                )
            )

            receipt_voteheads = list({thecollection.votehead.vote_head_name for thereceipt in querySetReceipts for thecollection in Collection.objects.filter(receipt=thereceipt)})
            pik_voteheads = list({pik.votehead.vote_head_name for pikReceipt in querysetPIK for pik in PaymentInKind.objects.filter(receipt=pikReceipt)})
            grant_voteheads = list({grant_item.votehead.vote_head_name for grant in querySetGrants for grant_item in GrantItem.objects.filter(grant=grant)})
            combined_voteheads = list(set(receipt_voteheads + pik_voteheads + grant_voteheads))

            print(f"List of voteheads is {combined_voteheads}")

            overall_votehead_amounts = defaultdict(Decimal)
            cash_overall_total = Decimal(0)
            bank_overall_total = Decimal(0)
            receipt_list = []


            if not month:
                opening_balance = Decimal(0.0)
                opencash = Decimal(0.0)
                openbank = Decimal(0.0)
            else:
                opencash = getBalance(accounttype, month, financialyear, school_id)["cash"]
                openbank = getBalance(accounttype, month, financialyear, school_id)["bank"]

            for dateinstance in listofdateofcreations:

                receipt_range = []
                receipt_cash = Decimal(opencash)
                receipt_bank = Decimal(openbank)
                thereceipt_voteheads = defaultdict(Decimal)


                #BURSARIES
                for bursary in querySetBursary:
                    if bursary.receipt_date == dateinstance:
                        bursary_cash = Decimal(0)
                        bursary_bank = Decimal(0)
                        bursary_total_amount = bursary.items.aggregate(total_amount=Sum('amount'))['total_amount']
                        method = "BANK" if bursary.paymentMethod and bursary.paymentMethod.is_cheque else "CASH" if bursary.paymentMethod and bursary.paymentMethod.is_cash else "NONE"
                        if method == "CASH" or method == "NONE":
                            bursary_cash += bursary_total_amount
                            cash_overall_total += bursary_total_amount
                        if method == "BANK":
                            bursary_bank += bursary_total_amount
                            bank_overall_total += bursary_total_amount
                        bursary_total = bursary_cash + bursary_bank

                        thevoteheads = defaultdict(Decimal)
                        for thevotehead in combined_voteheads:
                            thevoteheads[thevotehead] += Decimal(0)

                        receipt_list.append({
                                "date": dateinstance,
                                "description": f"{bursary.institution}",
                                "receipt_range": bursary.counter,
                                "cash": bursary_cash,
                                "bank": bursary_bank,
                                "total_amount": bursary_total,
                                "voteheads": thevoteheads,
                            })

                # GRANTS
                for grant in querySetGrants:
                    if grant.receipt_date == dateinstance:
                        grant_cash = Decimal(0)
                        grant_bank = Decimal(0)
                        grant_overall_amount = Decimal(grant.overall_amount)
                        method = "BANK" if grant.paymentMethod and grant.paymentMethod.is_cheque else "CASH" if grant.paymentMethod and grant.paymentMethod.is_cash else "NONE"
                        if method == "CASH" or method == "NONE":
                            grant_cash += grant_overall_amount
                            cash_overall_total += grant_overall_amount
                        if method == "BANK":
                            grant_bank += grant_overall_amount
                            bank_overall_total += grant_overall_amount
                        grant_total = grant_cash + grant_bank

                        thevoteheads = defaultdict(Decimal)
                        for thevotehead in combined_voteheads:

                            votehead_distribution = grant.voteheadamounts
                            for votehead_id, amount in votehead_distribution.items():
                                actualvotehead = VoteHead.objects.filter(id=votehead_id).first()
                                if actualvotehead and actualvotehead.vote_head_name == thevotehead:
                                    thevoteheads[actualvotehead.vote_head_name] += Decimal(amount)
                                    overall_votehead_amounts[actualvotehead.vote_head_name] += Decimal(amount)
                                else:
                                    thevoteheads[thevotehead] += Decimal(0)



                        receipt_list.append({
                                "date": dateinstance,
                                "description": f"{grant.institution}",
                                "receipt_range": grant.counter,
                                "cash": grant_cash,
                                "bank": grant_bank,
                                "total_amount": grant_total,
                                "voteheads": thevoteheads,
                            })



                # RECEIPTS
                for receipt in querySetReceipts:
                    if receipt.transaction_date == dateinstance:
                        receipt_overall_amount = Decimal(receipt.totalAmount)
                        method = "BANK" if receipt.payment_method and receipt.payment_method.is_cheque else "CASH" if receipt.payment_method and receipt.payment_method.is_cash else "NONE"
                        if method == "CASH" or method == "NONE":
                            receipt_cash += receipt_overall_amount
                            cash_overall_total += receipt_overall_amount
                        if method == "BANK":
                            receipt_bank += receipt_overall_amount
                            bank_overall_total += receipt_overall_amount

                        counter = receipt.counter
                        receipt_range.append(counter)

                        collections = Collection.objects.filter(receipt=receipt)
                        for collection in collections:

                            for thevotehead in combined_voteheads:
                                votehead_name = collection.votehead.vote_head_name
                                if votehead_name == thevotehead:
                                    thereceipt_voteheads[votehead_name] += Decimal(collection.amount)
                                    overall_votehead_amounts[votehead_name] += Decimal(collection.amount)
                                else:
                                    thereceipt_voteheads[thevotehead] += Decimal(0)


                for pikreceipt in querysetPIK:
                    if pikreceipt.receipt_date == dateinstance:
                        receipt_cash += Decimal(pikreceipt.totalAmount)
                        counter = pikreceipt.counter
                        receipt_range.append(counter)
                        cash_overall_total += Decimal(pikreceipt.totalAmount)

                    piks = PaymentInKind.objects.filter(receipt=pikreceipt)
                    for pik in piks:

                        for thevotehead in combined_voteheads:
                            votehead_name = pik.votehead.vote_head_name
                            if votehead_name == thevotehead:
                                thereceipt_voteheads[votehead_name] += Decimal(pik.amount)
                                overall_votehead_amounts[votehead_name] += Decimal(pik.amount)
                            else:
                                thereceipt_voteheads[thevotehead] += Decimal(0)



                receipt_receptrange = f"{min(receipt_range)} - {max(receipt_range)}" if receipt_range else "None"
                receipt_list.append({
                    "date": dateinstance,
                    "description": f"FEES",
                    "receipt_range": receipt_receptrange,
                    "cash": receipt_cash,
                    "bank": receipt_bank,
                    "total_amount": receipt_cash + receipt_bank,
                    "voteheads": thereceipt_voteheads,
                })




            # VOUCHERS
            listofVoucherDateCreations = sorted(set(querySetExpenses.values_list('voucher__paymentDate', flat=True).distinct()))

            voucher_votehead_list = list({voucher_item.votehead.vote_head_name for voucher_item in querySetExpenses })
            overall_votehead_amounts_voucher = defaultdict(Decimal)
            listofVouchers = []
            voucher_cash_overall_total = Decimal(0)
            voucher_bank_overall_total = Decimal(0)

            for dateinstance in listofVoucherDateCreations:
                for voucher in querySetExpenses:
                    voucher_cash = Decimal("0.0")
                    voucher_bank = Decimal("0.0")
                    amount = Decimal(voucher.amount)

                    if voucher.voucher.paymentDate == dateinstance:
                        method = "BANK" if voucher.voucher.payment_Method and voucher.voucher.payment_Method.is_cheque else "CASH" if voucher.voucher.payment_Method and voucher.voucher.payment_Method.is_cash else "NONE"
                        if method == "CASH" or method == "NONE":
                            voucher_cash += amount
                            voucher_cash_overall_total += amount
                        elif method == "BANK":
                            voucher_bank += amount
                            voucher_bank_overall_total += amount

                        thevoteheads = defaultdict(Decimal)

                        for thevotehead in voucher_votehead_list:
                            if voucher.votehead.vote_head_name  == thevotehead:
                                thevoteheads[voucher.votehead.vote_head_name] += amount
                                overall_votehead_amounts_voucher[voucher.votehead.vote_head_name] += amount
                            else:
                                thevoteheads[thevotehead] = Decimal(0)


                        receipient_type = voucher.voucher.recipientType
                        if receipient_type == "OTHER":
                            person = voucher.voucher.other
                        elif receipient_type == "STAFF":
                            person = f"{voucher.voucher.staff.fname} {voucher.voucher.staff.lname}"
                        else:
                            # person = f"{voucher.voucher.supplier.contactPerson}"
                            person = f"SUPPLIER"

                        listofVouchers.append(
                            {
                                "date": dateinstance,
                                "description": person,
                                "receipt_range": voucher.voucher.counter,
                                "cash": voucher_cash,
                                "bank": voucher_bank,
                                "total_amount": Decimal(voucher.amount),
                                "voteheads": thevoteheads,
                            }
                        )



            if not month:
                total_opening_balance = Decimal(0.0)
                opening_cash = Decimal(0.0)
                opening_bank = Decimal(0.0)
            else:
                total_opening_balance = getBalance(accounttype, month, financialyear, school_id)["total"]
                opening_cash = getBalance(accounttype, month, financialyear, school_id)["cash"]
                opening_bank = getBalance(accounttype, month, financialyear, school_id)["bank"]

            total_expense = voucher_cash_overall_total + voucher_bank_overall_total
            total_collection = Decimal(cash_overall_total) + Decimal(bank_overall_total)

            total_collectioncash = cash_overall_total
            total_collectionbank = bank_overall_total

            total_expensecash = voucher_cash_overall_total
            total_expensebank = voucher_bank_overall_total
            total_total_expense = Decimal(total_expensecash) + Decimal(total_expensebank),

            total_total_collection = Decimal(total_collectioncash) + Decimal(total_collectionbank)
            total_closing_balance = (Decimal(total_opening_balance) + Decimal(total_total_collection)) - Decimal(total_expense)

            closing_cash = Decimal(opening_cash) + Decimal(total_collectioncash) - Decimal(total_expensecash)
            closing_bank = Decimal(opening_cash) + Decimal(total_collectionbank) - Decimal(total_expensebank)

            thedata = {

                "receipts": receipt_list,
                "payments": listofVouchers,

                "opening_cash": opening_cash,
                "opening_bank": opening_bank,
                "total_opening_balance": total_opening_balance,

                "total_expense": total_total_expense,
                "total_collection": total_collection,

                "closing_cash": closing_cash,
                "closing_bank": closing_bank,
                "total_closing_balance": total_closing_balance,

                "total_collectioncash": total_collectioncash,
                "total_collectionbank": total_collectionbank,
                "total_total_collection": total_total_collection,

                "total_expensecash": total_expensecash,
                "total_expensebank": total_expensebank,
                "total_total_expense": total_total_expense,

                "total_payment_voteheads": overall_votehead_amounts_voucher,
                "total_collection_voteheads": overall_votehead_amounts,

            }


        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})





class FeeRegisterView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        try:
            school_id = self.check_school_id(request)
            if not school_id:
                return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

            student = request.GET.get('student')
            financialyear = request.GET.get('financialyear')
            academicyear = request.GET.get('academicyear')
            classes = request.GET.get('classes')
            stream = request.GET.get('stream')

            if not academicyear or academicyear == "" or academicyear == "null":
                return Response({'detail': f"Academic Year is a must"}, status=status.HTTP_400_BAD_REQUEST)

            if not student and not classes and not stream:
                return Response({'detail': f"Either of Student or Stream or Class should be passed"}, status=status.HTTP_400_BAD_REQUEST)

            student_List = []
            if student and student != "" and student != "null":
                try:
                    student = Student.objects.get(id=student, school_id=school_id)
                except ObjectDoesNotExist:
                    return Response({'detail': f"Invalid Student"}, status=status.HTTP_400_BAD_REQUEST)
                student_List.append(student)

            if classes and classes != "" and classes != "null":
                class_students = Student.objects.filter(school_id=school_id, current_Class__id = classes)
                if class_students:
                    for value in class_students:
                        student_List.append(value)

            if stream and stream != "" and stream != "null":
                stream_students = Student.objects.filter(current_Stream__id=stream, school_id=school_id)
                if stream_students:
                    for value in stream_students:
                        student_List.append(value)

            student_final_output = []

            for student in student_List:
                student_name = f"{student.first_name} - {student.last_name}"
                student_admission = student.admission_number
                student_class = student.current_Class
                student_stream = student.current_Stream
                student_id = student.id

                try:
                    year = get_object_or_404(AcademicYear, id=academicyear)
                except Exception as exception:
                    return Response({'detail': exception}, status=status.HTTP_400_BAD_REQUEST)

                querySetReceipts = Receipt.objects.filter(school_id=school_id, student=student, is_reversed = False)
                querysetPIK = PIKReceipt.objects.filter(school_id=school_id, student=student, is_posted=True)

                if financialyear and financialyear != "" and financialyear != "null":
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, financial_year__id=financialyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, financial_year__id=financialyear)

                if academicyear and academicyear != "" and academicyear != "null":
                    querySetReceipts = querySetReceipts.filter(school_id=school_id, year__id = academicyear)
                    querysetPIK = querysetPIK.filter(school_id=school_id, year__id = academicyear)


                listofdateofcreations = []
                listofdateofcreations.extend(querySetReceipts.values_list('transaction_date', flat=True))
                listofdateofcreations.extend(querysetPIK.values_list('receipt_date', flat=True))
                listofdateofcreations = list(set(listofdateofcreations))
                listofdateofcreations = list(listofdateofcreations)

                overall_balance_after = Decimal(0.0)
                universalvoteheadDictionary = {}
                total_collections = Decimal(0.0)

                dated_instances = []


                for index, dateinstance in enumerate(listofdateofcreations):

                    balanceTrackerQuerySet = BalanceTracker.objects.filter(
                        dateofcreation=dateinstance,
                        school_id=school_id, student=student
                    ).first()

                    if balanceTrackerQuerySet:
                        if index == len(listofdateofcreations) - 1:
                            #It is the last index
                            overall_balance_after = balanceTrackerQuerySet.balanceAfter


                    receipts = []

                    for receipt in querySetReceipts:
                        voteheadDictionary = {}
                        if receipt.transaction_date == dateinstance:
                            receipt_number = receipt.counter
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
                                    total_collections += collection.amount
                                    voteheadDictionary[f"{collection.votehead.vote_head_name}"] = collection.amount
                                else:
                                    total_collections += collection.amount
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
                        if pik.receipt_date == dateinstance:
                            receipt_number = pik.counter
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
                                    total_collections += pik.amount
                                    voteheadDictionary[f"{pik.votehead.vote_head_name}"] = pik.amount
                                else:
                                    total_collections += pik.amount
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


                universalvoteheadDictionary['overall_balance_after'] = overall_balance_after
                universalvoteheadDictionary['total_collections'] = total_collections

                invoiceList = Invoice.objects.filter(
                    student_id=student.id,
                    year=year,
                    school_id=school_id
                )


                student_voteheads = []
                for invoice in invoiceList:
                    votehead = invoice.votehead

                    receiptAmount = Collection.objects.filter(
                        receipt__is_reversed=False,
                        receipt__year=year, votehead=votehead,
                        school_id=school_id,
                        student=student
                    ).aggregate(Sum('amount'))['amount__sum'] or Decimal(0)

                    pikAmount = PIKReceipt.objects.filter(
                        is_posted = True,
                        year=year,
                        school_id=school_id,
                        student=student
                    ).aggregate(Sum('totalAmount'))['totalAmount__sum'] or Decimal(0)

                    amountpaid = Decimal(pikAmount) + Decimal(receiptAmount)
                    required_amount = invoice.amount - amountpaid
                    invoiced_amount = invoice.amount

                    student_voteheads.append(
                        {
                            "votehead": VoteHeadSerializer(votehead).data,
                            "name": votehead.vote_head_name,
                            "amount_paid": amountpaid,
                            "required_amount": required_amount,
                            "invoiced_amount": invoiced_amount,
                        }
                    )

                student_final_output.append(
                    {
                        "dated_student_instances": dated_instances,
                        "student": StudentSerializer(student).data,
                        "invoiced_voteheads": student_voteheads,
                        "totals": universalvoteheadDictionary
                    }
                )

            thedata = student_final_output

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": thedata})






def getMonthly_Balances(month, school_Id):
    themonth = month - 1

    collectionsAmount = Collection.objects.filter(receipt__is_reversed=False, transaction_date__month=themonth, school_id = school_Id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    piksAmount = PaymentInKind.objects.filter(receipt__is_posted = True, transaction_date__month=themonth,school_id = school_Id).aggregate(Sum('amount'))['amount__sum'] or Decimal(0.0)
    expensesAmount = Voucher.objects.filter(is_deleted=False, paymentDate__month=themonth,school_id = school_Id).aggregate(Sum('totalAmount'))['totalAmount__sum'] or Decimal(0.0)
    grantsAmount = Grant.objects.filter(deleted=False, receipt_date__month=themonth, school_id = school_Id).aggregate(Sum('overall_amount'))['overall_amount__sum'] or Decimal(0.0)

    totalCollections = Decimal(collectionsAmount) + Decimal(piksAmount) + Decimal(grantsAmount)
    totalExpenses = Decimal(expensesAmount)

    return {
        "totalCollections": totalCollections,
        "totalExpenses": totalExpenses,
    }



class LedgerView(SchoolIdMixin,  DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        financialyear = request.GET.get('financialyear')
        votehead = request.GET.get('votehead')

        if not financialyear or financialyear == "" or financialyear == "null" or not votehead or votehead == "" or votehead == "null":
            return Response({'detail': f"Both financial year and votehead are required"}, status=status.HTTP_400_BAD_REQUEST)

        check_if_object_exists(VoteHead, votehead)
        check_if_object_exists(FinancialYear, financialyear)


        grantsQuerySet = Grant.objects.filter(
            deleted=False,
            school_id=school_id,
            financial_year__id=financialyear
        )

        collectionQuerySet = Collection.objects.filter(
            receipt__is_reversed=False,
            school_id=school_id,
            receipt__financial_year__id=financialyear
        )

        pikQuerySet = PaymentInKind.objects.filter(
            receipt__is_posted=True,
            school_id=school_id,
            receipt__financial_year__id=financialyear
        )

        voucherQuerySet = Voucher.objects.filter(
            is_deleted=False,
            school_id=school_id,
            financial_year__id=financialyear
        )

        collectionQuerySet = collectionQuerySet if collectionQuerySet.exists() else Collection.objects.none()
        pikQuerySet = pikQuerySet if pikQuerySet.exists() else PaymentInKind.objects.none()
        voucherQuerySet = voucherQuerySet if voucherQuerySet.exists() else Voucher.objects.none()
        grantsQuerySet = grantsQuerySet if grantsQuerySet.exists() else Grant.objects.none()

        print(f"{len(collectionQuerySet)}")
        print(f"{len(pikQuerySet)}")
        print(f"{len(voucherQuerySet)}")
        print(f"{len(grantsQuerySet)}")

        date_list = []

        unique_collection_dates = collectionQuerySet.values_list('transaction_date', flat=True).distinct()
        unique_pik_dates = pikQuerySet.values_list('transaction_date', flat=True).distinct()
        unique_voucher_dates = voucherQuerySet.values_list('paymentDate', flat=True).distinct()
        unique_grant_dates = grantsQuerySet.values_list('receipt_date', flat=True).distinct()

        date_list.extend(unique_collection_dates)
        date_list.extend(unique_pik_dates)
        date_list.extend(unique_voucher_dates)
        date_list.extend(unique_grant_dates)

        date_list = list(set(date_list))

        actualFinancialYear = FinancialYear.objects.get(id = financialyear)
        monthlist  = FinancialYear.get_month_info(actualFinancialYear)

        print(f"{monthlist}")

        response_object = []

        for position, month in enumerate(monthlist):
            startdate = month['start_date']
            enddate = month['end_date']
            monthnumber = month['month_number']

            total_month_collection_amount = Decimal(0.0)


            for grant in grantsQuerySet:
                votehead_distribution = grant.voteheadamounts
                for votehead_id, amount in votehead_distribution.items():
                    theamount = Decimal(amount)
                    try:
                        if str(votehead_id) == votehead:
                            if grant.receipt_date.month == monthnumber:
                                collection_amount = theamount
                                total_month_collection_amount += collection_amount

                    except VoteHead.DoesNotExist:
                        pass



            for collection in collectionQuerySet:
                if str(collection.votehead.id) == votehead:
                    if collection.transaction_date.month == monthnumber:
                        collection_amount = collection.amount
                        total_month_collection_amount += collection_amount


            for pik in pikQuerySet:
                if str(pik.votehead.id) == votehead:
                    if pik.transaction_date.month == monthnumber:
                        pik_amount = pik.amount
                        total_month_collection_amount += pik_amount

            total_month_expenses_amount = Decimal(0.0)


            for voucher in voucherQuerySet:
                items = VoucherItem.objects.filter(school_id = school_id)
                for item in items:
                    if item.voucher == voucher:
                        print(f"Item voucher is same. Item votehead is {str(item.votehead.id)} and votehead sent is {votehead}")
                        if str(item.votehead.id) == votehead:
                            print(f"Voteheads are the same")
                            if item.voucher.paymentDate.month == monthnumber:
                                print(f"Item voucher month is same as month in search")
                                item_amount = item.amount
                                total_month_expenses_amount += item_amount

            if position == 0:
                previous_total_cr = total_month_collection_amount
                previous_total_dr = total_month_expenses_amount
            else:
                previous_month_balances = getMonthly_Balances(monthnumber, school_id)
                previous_total_cr = previous_month_balances['totalCollections']
                previous_total_dr = previous_month_balances['totalExpenses']

            response_object.append({
                "start_date": startdate,
                "month": monthnumber,
                "cr": total_month_collection_amount,
                "dr": total_month_expenses_amount,
                "previous_total_cr": previous_total_cr,
                "previous_total_dr": previous_total_dr
            })

        thedata = response_object

        return Response({"detail": thedata})









class TrialBalanceView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        financialyear = request.GET.get('financialyear')
        accounttype = request.GET.get('accounttype')
        month = request.GET.get('month')


        if not financialyear or financialyear=="" or financialyear == "null" or not accounttype or accounttype == "" or accounttype == "null" or not month or month == "" or month == "null":
            return Response({'detail': f"Account Type, Financial Year and Month are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            openingObject = OpeningClosingBalances.objects.get(school_id=school_id, financial_year__id=financialyear)
        except OpeningClosingBalances.DoesNotExist:
            openingObject = None

        cash_at_hand  = Decimal(0.0)
        cash_at_bank  = Decimal(0.0)

        if openingObject:
            cash_at_hand = openingObject.opening_cash_at_hand
            cash_at_bank = openingObject.opening_cash_at_bank

        votehead_list = VoteHead.objects.filter(school_id=school_id)

        print(f"Votehead list is {votehead_list}")
        collectionvoteheadDictionary = {}

        total_cash = Decimal(0.0)
        total_bank = Decimal(0.0)
        total_expense = Decimal(0.0)

        for votehead in votehead_list:


            grants = Grant.objects.filter(
                deleted = False,
                school_id=school_id,
                financial_year=financialyear,
                receipt_date__month__lte=month
            )

            for grant in grants:

                votehead_distribution = grant.voteheadamounts

                for votehead_id, amount in votehead_distribution.items():
                    theamount = Decimal(amount)

                    try:
                        actualvotehead = VoteHead.objects.get(id=votehead_id)

                        if not collectionvoteheadDictionary.get(f"{votehead_id}"):
                            collectionvoteheadDictionary[f"{votehead_id}"] = {}

                            if not collectionvoteheadDictionary.get(f"{votehead_id}").get("cramount"):
                                collectionvoteheadDictionary[f"{votehead_id}"]["cramount"] = Decimal(0.0)
                            if not collectionvoteheadDictionary.get(f"{votehead_id}").get("dramount"):
                                collectionvoteheadDictionary[f"{votehead_id}"]["dramount"] = Decimal(0.0)

                            collectionvoteheadDictionary[f"{votehead_id}"]["name"] = actualvotehead.vote_head_name
                            collectionvoteheadDictionary[f"{votehead_id}"][
                                "lf_number"] = actualvotehead.ledget_folio_number_lf

                        if actualvotehead == votehead:
                            method = "NONE"
                            if grant.paymentMethod:
                                method = "BANK" if grant.paymentMethod.is_cheque else "CASH" if grant.paymentMethod.is_cash else "BANK" if grant.paymentMethod.is_bank else "NONE"
                            if method == "CASH":
                                total_cash += Decimal(theamount)
                            if method == "BANK":
                                total_bank += Decimal(theamount)
                            if method == "NONE":
                                total_cash += Decimal(theamount)
                            collectionvoteheadDictionary[f"{votehead_id}"]["cramount"] += theamount

                    except VoteHead.DoesNotExist:
                        pass








            piks = PaymentInKind.objects.filter(
                receipt__is_posted=True,
                school_id=school_id,
                receipt__financial_year=financialyear,
                transaction_date__month__lte=month
            )

            print(f"pik {len(piks)}")

            for pik in piks:
                if not collectionvoteheadDictionary.get(f"{pik.votehead.id}"):
                    collectionvoteheadDictionary[f"{pik.votehead.id}"] = {}
                    collectionvoteheadDictionary[f"{pik.votehead.id}"]["name"] = pik.votehead.vote_head_name

                    if not collectionvoteheadDictionary.get(f"{pik.votehead.id}").get("cramount"):
                        collectionvoteheadDictionary[f"{pik.votehead.id}"]["cramount"] = Decimal(0.0)
                    if not collectionvoteheadDictionary.get(f"{pik.votehead.id}").get("dramount"):
                        collectionvoteheadDictionary[f"{pik.votehead.id}"]["dramount"] = Decimal(0.0)

                    collectionvoteheadDictionary[f"{pik.votehead.id}"]["lf_number"] = pik.votehead.ledget_folio_number_lf
                if pik.votehead == votehead:
                    total_cash += pik.amount
                    collectionvoteheadDictionary[f"{pik.votehead.id}"]["cramount"] += pik.amount


            collections = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                receipt__financial_year=financialyear,
                transaction_date__month__lte=month
            )

            print(f"{school_id}")
            print(f"Collections {len(collections)}")


            for collection in collections:
                if not collectionvoteheadDictionary.get(f"{collection.votehead.id}"):
                    collectionvoteheadDictionary[f"{collection.votehead.id}"] = {}

                    if not collectionvoteheadDictionary.get(f"{collection.votehead.id}").get("cramount"):
                     collectionvoteheadDictionary[f"{collection.votehead.id}"]["cramount"] = Decimal(0.0)
                    if not collectionvoteheadDictionary.get(f"{collection.votehead.id}").get("dramount"):
                      collectionvoteheadDictionary[f"{collection.votehead.id}"]["dramount"] = Decimal(0.0)

                    collectionvoteheadDictionary[f"{collection.votehead.id}"]["name"] = collection.votehead.vote_head_name
                    collectionvoteheadDictionary[f"{collection.votehead.id}"]["lf_number"] = collection.votehead.ledget_folio_number_lf

                if collection.votehead == votehead:
                    receipt = collection.receipt
                    method = "NONE"
                    if receipt.payment_method:
                        method = "BANK" if receipt.payment_method.is_cheque else "CASH" if receipt.payment_method.is_cash else "BANK" if receipt.payment_method.is_bank else "NONE"
                    if method == "CASH":
                        total_cash += Decimal(collection.amount)
                    if method == "BANK":
                        total_bank += Decimal(collection.amount)
                    if method == "NONE":
                        total_cash += Decimal(collection.amount)
                    collectionvoteheadDictionary[f"{collection.votehead.id}"]["cramount"] += collection.amount




            expenses = VoucherItem.objects.filter(
                voucher__is_deleted=False,
                school_id=school_id,
                voucher__financial_year=financialyear,
                voucher__paymentDate__month__lte=month
            )

            print(f"{expenses}")

            for voucher_item in expenses:
                if not collectionvoteheadDictionary.get(f"{voucher_item.votehead.id}"):
                    collectionvoteheadDictionary[f"{voucher_item.votehead.id}"] = {}
                    collectionvoteheadDictionary[f"{voucher_item.votehead.id}"]["name"] = voucher_item.votehead.vote_head_name
                    if not collectionvoteheadDictionary.get(f"{voucher_item.votehead.id}").get("cramount"):
                     collectionvoteheadDictionary[f"{voucher_item.votehead.id}"]["cramount"] = Decimal(0.0)
                    if not collectionvoteheadDictionary.get(f"{voucher_item.votehead.id}").get("dramount"):
                      collectionvoteheadDictionary[f"{voucher_item.votehead.id}"]["dramount"] = Decimal(0.0)
                    collectionvoteheadDictionary[f"{voucher_item.votehead.id}"]["lf_number"] = voucher_item.votehead.ledget_folio_number_lf

                if voucher_item.votehead == votehead:
                    total_expense += Decimal(voucher_item.amount)

                    collectionvoteheadDictionary[f"{voucher_item.votehead.id}"]["dramount"] += voucher_item.amount


        overall_total = Decimal(cash_at_hand) + Decimal(cash_at_bank) + Decimal(total_cash) + Decimal(total_bank)

        collection_voteheads_list = []


        budget = Budget.objects.filter(financialYear=financialyear, school_id=school_id).first()

        for votehead, data in collectionvoteheadDictionary.items():
            if budget:
                budget_items = budget.budget_items

                if str(votehead) in budget_items:
                    votehead_data = Decimal(budget_items[str(votehead)])
                else:
                    votehead_data = Decimal("0")
            else:
                votehead_data = Decimal("0")

            collection_voteheads_list.append(
                {
                    "votehead": votehead,
                    "cramount": data["cramount"],
                    "dramount": data["dramount"],
                    "budget_estimate": votehead_data,
                    "available_balance": votehead_data - Decimal(data["dramount"]),
                    "name": data["name"],
                    "lf_number": data["lf_number"],
                }
            )

        save_object = {
            "cash_at_hand": cash_at_hand,
            "cash_at_bank": cash_at_bank,
            "voteheads": collection_voteheads_list,
            "closing_cash": total_cash,
            "closing_bank": total_bank,
            "overall_total": overall_total
        }

        return Response({"detail": save_object})








class NotesView(SchoolIdMixin, DefaultMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        financialyear = request.GET.get('financialyear')

        if not financialyear or financialyear=="":
            return Response({'detail': f"Financial Year is required"}, status=status.HTTP_400_BAD_REQUEST)

        accountTypeList = AccountType.objects.filter(school=school_id) or []
        votehead_list = VoteHead.objects.filter(school_id=school_id)


        try:
            current_financial_year = FinancialYear.objects.get(school = school_id, is_current = True)
        except ObjectDoesNotExist:
            return Response({'detail': f"Current financial year has not been set for this school"}, status=status.HTTP_400_BAD_REQUEST)

        financial_year_list = FinancialYear.objects.filter(school =school_id).order_by('dateofcreation')
        financial_year_list_as_list = list(financial_year_list)

        try:
            current_financial_year_index = financial_year_list_as_list.index(current_financial_year)
        except ValueError:
            current_financial_year_index = None

        if current_financial_year_index > 0:
            previous_year = financial_year_list[current_financial_year_index - 1]
        else:
            previous_year = None



        collections_list = []
        expenses_list = []
        my_bank_account_list = []
        cash_in_hand_list = []
        accounts_receivable = []
        accounts_payables = []
        balance_brought_forward = []

        #COLLECTIONS
        for accountType in accountTypeList:
            accountype_name  = accountType.account_type_name

            collection_votehead = {}
            current_collection_total = Decimal(0.0)
            previous_collection_total = Decimal(0.0)


            # COLLECTION - COLLECTIONS
            current_grants = Grant.objects.filter(school_id=school_id, deleted=False,bankAccount__account_type=accountType,financial_year__id=financialyear) or []

            for grant in current_grants:
                amount = grant.overall_amount

                votehead_distribution = grant.voteheadamounts
                for votehead_id, amount in votehead_distribution.items():
                    try:
                        actualvotehead = VoteHead.objects.get(id=votehead_id)
                        if actualvotehead in votehead_list:
                            votehead_name = actualvotehead.vote_head_name
                            if not collection_votehead.get(votehead_name):
                                collection_votehead[votehead_name] = {}
                                collection_votehead[votehead_name]["name"] = votehead_name
                                collection_votehead[votehead_name]["amount"] = Decimal(amount)
                                current_collection_total += Decimal(amount)
                            else:
                                if "amount" not in collection_votehead[votehead_name]:
                                    collection_votehead[votehead_name]["amount"] = Decimal(amount)
                                else:
                                    collection_votehead[votehead_name]["amount"] += Decimal(amount)
                                current_collection_total += Decimal(amount)

                    except VoteHead.DoesNotExist:
                        pass



            if previous_year:
                previous_year_collections = Grant.objects.filter(school_id=school_id, deleted=False,
                                                         bankAccount__account_type=accountType,
                                                         financial_year=previous_year) or []
                for grant in previous_year_collections:
                    amount = grant.totalAmount

                    votehead_distribution = grant.voteheadamounts
                    for votehead_id, amount in votehead_distribution.items():
                        try:
                            actualvotehead = VoteHead.objects.get(id=votehead_id)
                            if actualvotehead in votehead_list:
                                votehead_name = actualvotehead.vote_head_name
                                if not collection_votehead.get(votehead_name):
                                    collection_votehead[votehead_name] = {}
                                    collection_votehead[votehead_name]["name"] = votehead_name
                                    collection_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                                    previous_collection_total += Decimal(amount)
                                else:
                                    if "amount" not in collection_votehead[votehead_name]:
                                        collection_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                                    else:
                                        collection_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                                    previous_collection_total += Decimal(amount)

                        except VoteHead.DoesNotExist:
                            pass






            #COLLECTION - COLLECTIONS
            current_collections = Collection.objects.filter(school_id = school_id, receipt__is_reversed = False, receipt__bank_account__account_type = accountType, receipt__financial_year__id = financialyear) or []
            for collection in current_collections:
                amount = collection.amount
                for votehead in votehead_list:
                    if collection.votehead == votehead:
                        votehead_name = votehead.vote_head_name
                        if not collection_votehead.get(votehead_name):
                            collection_votehead[votehead_name] = {}
                            collection_votehead[votehead_name]["name"] = votehead_name
                            collection_votehead[votehead_name]["amount"] = Decimal(amount)
                            current_collection_total += Decimal(amount)
                        else:
                            if "amount" not in collection_votehead[votehead_name]:
                                collection_votehead[votehead_name]["amount"] = Decimal(amount)
                            else:
                                collection_votehead[votehead_name]["amount"] += Decimal(amount)
                            current_collection_total += Decimal(amount)

            if previous_year:
                previous_year_collections = Collection.objects.filter(school_id = school_id, receipt__is_reversed = False, receipt__bank_account__account_type = accountType, receipt__financial_year = previous_year) or []
                for collection in previous_year_collections:
                    amount = collection.amount
                    for votehead in votehead_list:
                        if collection.votehead == votehead:
                            votehead_name = votehead.vote_head_name
                            if not collection_votehead.get(votehead_name):
                                collection_votehead[votehead_name] = {}
                                collection_votehead[votehead_name]["name"] = votehead_name
                                collection_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                                previous_collection_total += Decimal(amount)

                            else:
                                if "previous_amount" not in collection_votehead[votehead_name]:
                                    collection_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                                else:
                                    collection_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                                previous_collection_total += Decimal(amount)

            #COLLECTION - PIKS
            current_PIKS = PaymentInKind.objects.filter(receipt__is_posted=True, school_id=school_id,
                                                         receipt__bank_account__account_type=accountType,
                                                         receipt__financial_year__id=financialyear) or []
            for pik in current_PIKS:
                amount = pik.amount
                for votehead in votehead_list:
                    if pik.votehead == votehead:
                        votehead_name = votehead.vote_head_name
                        if not collection_votehead.get(votehead_name):
                            collection_votehead[votehead_name] = {}
                            collection_votehead[votehead_name]["name"] = votehead_name
                            collection_votehead[votehead_name]["amount"] = Decimal(amount)
                            current_collection_total += Decimal(amount)
                        else:
                            if "amount" not in collection_votehead[votehead_name]:
                                collection_votehead[votehead_name]["amount"] = Decimal(amount)
                            else:
                                collection_votehead[votehead_name]["amount"] += Decimal(amount)
                            current_collection_total += Decimal(amount)

            if previous_year:
                previous_year_piks = PaymentInKind.objects.filter(receipt__is_posted=True, school_id=school_id,
                                                         receipt__bank_account__account_type=accountType,
                                                         receipt__financial_year=previous_year) or []
                for pik in previous_year_piks:
                    amount = pik.amount
                    for votehead in votehead_list:
                        if pik.votehead == votehead:
                            votehead_name = votehead.vote_head_name
                            if not collection_votehead.get(votehead_name):
                                collection_votehead[votehead_name] = {}
                                collection_votehead[votehead_name]["name"] = votehead_name
                                collection_votehead[votehead_name]["amount"] = Decimal(amount)
                                previous_collection_total += Decimal(amount)
                            else:
                                if "amount" not in collection_votehead[votehead_name]:
                                    collection_votehead[votehead_name]["amount"] = Decimal(amount)
                                else:
                                    collection_votehead[votehead_name]["amount"] += Decimal(amount)
                                previous_collection_total += Decimal(amount)



            collection_votehead_list  = []

            for key, value in collection_votehead.items():
                item = {"name": key, "amount": value.get("amount", 0.0)}
                previous_amount = value.get("previous_amount")
                if previous_amount is not None:
                    item["previous_amount"] = previous_amount
                collection_votehead_list.append(item)

            send = {
                "account_type_name": accountype_name,
                "current_collection_total": current_collection_total,
                "previous_collection_total": previous_collection_total,
                "collection_votehead": collection_votehead_list,
            }

            collections_list.append(send)



        #EXPENSES
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name
            expenses_votehead = {}
            current_expenses_total = Decimal(0.0)
            previous_expenses_total = Decimal(0.0)

            current_expenses = Voucher.objects.filter(is_deleted=False, school_id = school_id, bank_account__account_type = accountType, financial_year__id = financialyear) or []
            for expense in current_expenses:
                amount = expense.totalAmount
                for votehead in votehead_list:
                    votehead_name = votehead.vote_head_name
                    if not expenses_votehead.get(votehead_name):
                        expenses_votehead[votehead_name] = {}
                        expenses_votehead[votehead_name]["name"] = votehead_name
                        expenses_votehead[votehead_name]["amount"] = Decimal(amount)
                        current_expenses_total += Decimal(amount)
                    else:
                        if "amount" not in expenses_votehead[votehead_name]:
                            expenses_votehead[votehead_name]["amount"] = Decimal(amount)
                        else:
                            expenses_votehead[votehead_name]["amount"] += Decimal(amount)
                        current_expenses_total += Decimal(amount)

            if previous_year:
                previous_year_expenses = Voucher.objects.filter(is_deleted=False, bank_account__account_type = accountType, school_id = school_id, financial_year = previous_year) or []
                for expense in previous_year_expenses:
                    amount = expense.totalAmount
                    for votehead in votehead_list:
                        votehead_name = votehead.vote_head_name
                        if not expenses_votehead.get(votehead_name):
                            expenses_votehead[votehead_name] = {}
                            expenses_votehead[votehead_name]["name"] = votehead_name
                            expenses_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                            previous_expenses_total += Decimal(amount)

                        else:
                            if "previous_amount" not in expenses_votehead[votehead_name]:
                                expenses_votehead[votehead_name]["previous_amount"] = Decimal(amount)
                            else:
                                expenses_votehead[votehead_name]["previous_amount"] += Decimal(amount)
                            previous_expenses_total += Decimal(amount)


                expenses_votehead_list = []

                for key, value in expenses_votehead.items():
                    item = {"name": key, "amount": value.get("amount", None)}
                    previous_amount = value.get("previous_amount", None)
                    if previous_amount is not None:
                        item["previous_amount"] = previous_amount
                    expenses_votehead_list.append(item)

                send = {
                    "account_type_name": accountype_name,
                    "current_expenses_total": current_expenses_total,
                    "previous_expenses_total": previous_expenses_total,
                    "expenses_votehead": expenses_votehead_list,
                }
                expenses_list.append(send)



        #BANK ACCOUNTS
        bank_account_list = BankAccount.objects.filter(school=school_id) or []

        for bank_account in bank_account_list:
            bank_account_name = bank_account.account_name
            bank_account_number = bank_account.account_number
            bank_account_currency = bank_account.currency.currency_name

            account_list = []

            for accountType in accountTypeList:
                accountype_name = accountType.account_type_name
                current_bank_total = Decimal(0.0)
                previous_bank_total = Decimal(0.0)

                querysetGrants = Grant.objects.filter(
                    deleted=False,
                    school_id=school_id,
                    bankAccount__account_type = accountType,
                    financial_year=financialyear,
                    bankAccount = bank_account
                ).aggregate(result=Sum('overall_amount'))

                grants_amount_sum = querysetGrants.get('result', Decimal('0.0')) if querysetGrants.get(
                    'result') is not None else Decimal('0.0')

                receiptsQuerySet = Receipt.objects.filter(
                    is_reversed = False,
                    account_type=accountType,
                    school_id=school_id,
                    bank_account=bank_account,
                    financial_year=financialyear
                ).aggregate(result=Sum('totalAmount'))

                receipt_amount_sum = receiptsQuerySet.get('result', Decimal('0.0')) if receiptsQuerySet.get(
                    'result') is not None else Decimal('0.0')

                pikQuerySet = PIKReceipt.objects.filter(
                    is_posted=True,
                    bank_account__account_type=accountType,
                    school_id=school_id,
                    bank_account=bank_account,
                    financial_year=financialyear
                ).aggregate(result=Sum('totalAmount'))

                pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet.get(
                    'result') is not None else Decimal('0.0')

                print(f"{receipt_amount_sum}  -   {pik_receipt_sum}")

                current_bank_total =  Decimal(receipt_amount_sum) +  Decimal(pik_receipt_sum) + Decimal(grants_amount_sum)


                if previous_year:
                    querysetGrants = Grant.objects.filter(
                        deleted=False,
                        school_id=school_id,
                        bankAccount__account_type=accountType,
                        financial_year=previous_year,
                        bankAccount=bank_account
                    ).aggregate(result=Sum('overall_amount'))

                    grants_amount_sum = querysetGrants.get('result', Decimal('0.0')) if querysetGrants.get(
                        'result') is not None else Decimal('0.0')

                    receiptsQuerySet = Receipt.objects.filter(
                        is_reversed=False,
                        account_type=accountType,
                        bank_account=bank_account,
                        financial_year=previous_year,
                        school_id=school_id
                    ).aggregate(result=Sum('totalAmount'))

                    receipt_amount_sum = receiptsQuerySet.get('result', Decimal('0.0')) if receiptsQuerySet.get(
                        'result') is not None else Decimal('0.0')

                    pikQuerySet = PIKReceipt.objects.filter(
                        is_posted=True,
                        bank_account__account_type=accountType,
                        bank_account=bank_account,
                        financial_year=previous_year,
                        school_id=school_id
                    ).aggregate(result=Sum('totalAmount'))

                    pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet.get(
                        'result') is not None else Decimal('0.0')

                    previous_bank_total = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum) + Decimal(grants_amount_sum)

                    send = {
                            "account_type_name": accountype_name,
                            "current_bank_total": current_bank_total,
                            "previous_bank_total": previous_bank_total,
                        }
                    account_list.append(send)

                my_bank_account_list.append({
                    "bank_account_name": bank_account_name,
                    "bank_account_number": bank_account_number,
                    "bank_account_currency": bank_account_currency,
                    "accounts_for_bank": account_list
                })




        #CASH IN HAND
        for accountType in accountTypeList:
            accountype_name = accountType.account_type_name

            current_cash_in_hand = getBalancesByAccount(accountType, financialyear, school_id)['cash']
            previous_cash_in_hand = getBalancesByAccount(accountType, previous_year, school_id)['cash']

            send = {
                "account_type_name": accountype_name,
                "current_cash_in_hand": current_cash_in_hand,
                "previous_cash_in_hand": previous_cash_in_hand,
            }

            cash_in_hand_list.append(send)



        #ACCOUNT RECEIVABLES INVOICES
        arrears_current_bank_total = Decimal(0.0)
        arrears_previous_bank_total = Decimal(0.0)

        querysetGrants = Grant.objects.filter(
            deleted=False,
            financial_year=financialyear,
            school_id=school_id
        ).aggregate(result=Sum('overall_amount'))
        grant_amount_sum = querysetGrants.get('result', Decimal('0.0')) if querysetGrants.get(
            'result') is not None else Decimal('0.0')

        receiptsQuerySet = Receipt.objects.filter(
            school_id=school_id,
            financial_year=financialyear,
            is_reversed = False
        ).aggregate(result=Sum('totalAmount'))

        receipt_amount_sum = receiptsQuerySet.get('result', Decimal('0.0')) if receiptsQuerySet.get(
            'result') is not None else Decimal('0.0')

        pikQuerySet = PIKReceipt.objects.filter(
            is_posted=True,
            school_id=school_id,
            financial_year=financialyear
        ).aggregate(result=Sum('totalAmount'))

        pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet.get(
            'result') is not None else Decimal('0.0')
        arrears_current_bank_total = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum) + Decimal(grant_amount_sum)


        if previous_year:

            querysetGrants = Grant.objects.filter(
                deleted=False,
                financial_year=previous_year,
                school_id=school_id
            ).aggregate(result=Sum('overall_amount'))
            grant_amount_sum = querysetGrants.get('result', Decimal('0.0')) if querysetGrants.get(
                'result') is not None else Decimal('0.0')

            receiptsQuerySet = Receipt.objects.filter(
                school_id=school_id,
                financial_year=previous_year,
                is_reversed=False
            ).aggregate(result=Sum('totalAmount'))

            receipt_amount_sum = receiptsQuerySet.get('result', Decimal('0.0')) if receiptsQuerySet.get(
                'result') is not None else Decimal('0.0')

            pikQuerySet = PIKReceipt.objects.filter(
                is_posted=True,
                school_id=school_id,
                financial_year=previous_year
            ).aggregate(result=Sum('totalAmount'))

            pik_receipt_sum = pikQuerySet.get('result', Decimal('0.0')) if pikQuerySet.get(
                'result') is not None else Decimal('0.0')
            arrears_previous_bank_total = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum) + Decimal(grant_amount_sum)

        sendback = {
            "arrears_current_bank_total": arrears_current_bank_total,
            "arrears_previous_bank_total": arrears_previous_bank_total
        }

        accounts_receivable.append(sendback)




        #ACCOUNT PAYABLES
        current_collection_amount_sum = Decimal(0.0)
        previous_collection_amount_sum = Decimal(0.0)
        collectionQuerySet = Collection.objects.filter(
            receipt__is_reversed=False,
            school_id=school_id,
            is_overpayment = True,
            receipt__financial_year=financialyear
        ).aggregate(result=Sum('amount'))

        current_collection_amount_sum = collectionQuerySet.get('result', Decimal('0.0')) if collectionQuerySet.get('result') is not None else Decimal('0.0')

        if previous_year:
            collectionQuerySet = Collection.objects.filter(
                receipt__is_reversed=False,
                school_id=school_id,
                is_overpayment = True,
                receipt__financial_year=previous_year
            ).aggregate(result=Sum('amount'))

            previous_collection_amount_sum = collectionQuerySet.get('result', Decimal('0.0')) if collectionQuerySet.get(
                'result') is not None else Decimal('0.0')

        sendback = {
            "current_collection_amount_sum": current_collection_amount_sum,
            "previous_collection_amount_sum": previous_collection_amount_sum
        }

        accounts_payables.append(sendback)



        #FUND BALANCE BROUGHT FORWARD
        cash_balances_current = getBalancesByFinancialYear(financialyear, school_id)['cash']
        bank_balances_previous = getBalancesByFinancialYear(previous_year, school_id)['cash']
        receivables_current = accounts_receivable[0]['arrears_current_bank_total']
        receivables_previous = accounts_receivable[0]['arrears_previous_bank_total']
        payables_current = accounts_payables[0]['current_collection_amount_sum']
        payables_previous = accounts_payables[0]['previous_collection_amount_sum']

        print(cash_balances_current, receivables_current, payables_current)

        current_totals =Decimal(cash_balances_current) + Decimal(receivables_current) + Decimal(payables_current)
        previous_totals =Decimal(bank_balances_previous) + Decimal(receivables_previous) + Decimal(payables_previous)

        send = {
            "cash_balances_current": cash_balances_current,
            "bank_balances_previous": bank_balances_previous,
            #"receivables_current": receivables_current,
            "receivables_current": {},
            #"receivables_previous": receivables_previous,
            "receivables_previous": {},
            #"payables_current": payables_current,
            "payables_current": {},
            #"payables_previous": payables_previous,
            "payables_previous": {},
            #"current_totals": current_totals,
            "current_totals": Decimal(0.0),
            #"previous_totals": previous_totals,
            "previous_totals": Decimal(0.0),
        }

        balance_brought_forward.append(send)

        print(f"{collections_list}")
        print("\n")

        print(f"{expenses_list}")
        print("\n")

        print(f"{my_bank_account_list}")
        print("\n")

        print(f"{cash_in_hand_list}")
        print("\n")

        print(f"{accounts_receivable}")
        print("\n")

        print(f"{accounts_receivable}")
        print("\n")

        full = {
            "collections_list": collections_list,
            "expenses_list": expenses_list,
            "cash_in_hand_list": cash_in_hand_list,
            "accounts_receivable": accounts_receivable,
            "accounts_payables": accounts_payables,
            "balance_brought_forward": balance_brought_forward,
            "my_bank_account_list": my_bank_account_list
        }

        return Response({"detail": full})