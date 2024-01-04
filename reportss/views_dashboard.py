# Create your views here.
from copy import copy
from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.response import Response

from academic_year.models import AcademicYear
from appcollections.models import Collection
from classes.models import Classes
from invoices.models import Invoice
from payment_in_kinds.models import PaymentInKind
from students.models import Student
from students.serializers import StudentSerializer
from utils import SchoolIdMixin
from voteheads.models import VoteHead
from voucher_items.models import VoucherItem


class DashboardView(SchoolIdMixin, generics.GenericAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            accountType = request.GET.get('accountType')
            range_start_date = request.GET.get('range_start_date')
            range_end_date = request.GET.get('range_end_date')

            try:
                current_academic_year = AcademicYear.objects.get(is_current=True, school_id=school_id)
            except ObjectDoesNotExist:
                current_academic_year = None

            if not accountType:
                return Response({'detail': f"Account Type is required"}, status=status.HTTP_400_BAD_REQUEST)

            receiptsQuerySet = Collection.objects.filter(
                school_id=school_id,
                receipt__is_reversed=False,
                receipt__account_type=accountType
            )
            pikQuerySet = PaymentInKind.objects.filter(
                school_id=school_id,
                receipt__is_posted=True,
                receipt__bank_account__account_type=accountType
            )
            expensesVouchers = VoucherItem.objects.filter(
                school_id=school_id,
                voucher__is_deleted=False,
                voucher__bank_account__account_type=accountType
            )

            if range_start_date and range_start_date != "":
                start_date = datetime.strptime(range_start_date, '%Y-%m-%d')
                receiptsQuerySet = receiptsQuerySet.filter(transaction_date__gte=range_start_date)
                pikQuerySet = pikQuerySet.filter(transaction_date__gte=range_start_date)
                expensesVouchers = expensesVouchers.filter(voucher__paymentDate__gte=range_start_date)

            if range_end_date and range_end_date != "":
                end_date = datetime.strptime(range_end_date, '%Y-%m-%d')
                receiptsQuerySet = receiptsQuerySet.filter(transaction_date__lte=range_start_date)
                pikQuerySet = pikQuerySet.filter(transaction_date__lte=range_start_date)
                expensesVouchers = expensesVouchers.filter(voucher__paymentDate__lte=range_start_date)

            receiptsQuerySet_aggregate = receiptsQuerySet.aggregate(result=Sum('amount'))
            pikQuerySet_aggregate = pikQuerySet.aggregate(result=Sum('amount'))
            expensesVouchers_aggregate = expensesVouchers.aggregate(result=Sum('amount'))

            receipt_amount_sum = receiptsQuerySet_aggregate.get('result', Decimal('0.0')) if receiptsQuerySet_aggregate.get(
                'result') is not None else Decimal('0.0')
            pik_receipt_sum = pikQuerySet_aggregate.get('result', Decimal('0.0')) if pikQuerySet_aggregate.get(
                'result') is not None else Decimal('0.0')
            expensesVoucher_sum = expensesVouchers_aggregate.get('result', Decimal('0.0')) if expensesVouchers_aggregate.get(
                'result') is not None else Decimal('0.0')

            list_of_forms = Classes.objects.filter(school_id=school_id) or []
            list_of_voteheads = VoteHead.objects.filter(school_id=school_id) or []
            students = Student.objects.filter(school_id = school_id) or []

            total_collections = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)
            total_vouchers = expensesVoucher_sum
            form_collections_percentages = []
            income_vs_expense = []
            students_number = len(students)

            for form in list_of_forms:
                form_name = form.classname

                receipts_query_set = copy(receiptsQuerySet)
                pik_query_set = copy(pikQuerySet)

                receipts_query_set = receipts_query_set.filter(receipt__student_class=form)
                pik_query_set = pik_query_set.filter(receipt__student_class=form)

                receipts_query_set_aggregate = receipts_query_set.aggregate(result=Sum('amount'))
                pik_query_set_aggregate = pik_query_set.aggregate(result=Sum('amount'))

                receipt_amount_sum = receipts_query_set_aggregate.get('result',Decimal('0.0')) if receipts_query_set_aggregate.get(
                    'result') is not None else Decimal('0.0')
                pik_receipt_sum = pik_query_set_aggregate.get('result', Decimal('0.0')) if pik_query_set_aggregate.get(
                    'result') is not None else Decimal('0.0')
                totalCollections = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)


                if current_academic_year:
                    invoicedAmountQuerySet = Invoice.objects.filter(
                        school_id=school_id,
                        year=current_academic_year
                    )
                    invoicedAmountQuerySet_aggregate = invoicedAmountQuerySet.aggregate(result=Sum('amount'))
                    invoiced_amount_sum = invoicedAmountQuerySet_aggregate.get('result',Decimal('0.0')) if invoicedAmountQuerySet_aggregate.get(
                        'result') is not None else Decimal('0.0')

                    percentage = (totalCollections/invoiced_amount_sum) * 100
                    rounded_percentage = round(percentage)

                    to_Send = {
                        "form_name": form_name,
                        "collections": totalCollections,
                        "invoiced": invoiced_amount_sum,
                        "percentage": rounded_percentage
                    }
                    form_collections_percentages.append(to_Send)

            for votehead in list_of_voteheads:
                votehead_name = votehead.vote_head_name

                receipts_query_set = copy(receiptsQuerySet)
                pik_query_set = copy(pikQuerySet)
                expenses_query_set = copy(expensesVouchers)

                receipts_query_set = receipts_query_set.filter(votehead=votehead)
                pik_query_set = pik_query_set.filter(votehead=votehead)
                expenses_query_set = expenses_query_set.filter(votehead=votehead)

                receipts_query_set_aggregate = receipts_query_set.aggregate(result=Sum('amount'))
                pik_query_set_aggregate = pik_query_set.aggregate(result=Sum('amount'))
                expenses_query_set = expenses_query_set.aggregate(result=Sum('amount'))

                receipt_amount_sum = receipts_query_set_aggregate.get('result',Decimal('0.0')) if receipts_query_set_aggregate.get(
                    'result') is not None else Decimal('0.0')
                pik_receipt_sum = pik_query_set_aggregate.get('result', Decimal('0.0')) if pik_query_set_aggregate.get(
                    'result') is not None else Decimal('0.0')
                totalCollections = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)

                total_expenses = expenses_query_set.get('result', Decimal('0.0')) if expenses_query_set.get(
                    'result') is not None else Decimal('0.0')

                tosend = {
                    "voteheadname" : votehead_name,
                    "totalCollections" : totalCollections,
                    "total_expenses" : total_expenses,
                }
                income_vs_expense.append(tosend)

            toreturn = {
                "total_collections": total_collections,
                "total_vouchers": total_vouchers,
                "form_collections_percentages": form_collections_percentages,
                "income_vs_expense": income_vs_expense,
                "students_number": students_number
            }

        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": toreturn})