# Create your views here.
from copy import copy

from _decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import status, generics
from rest_framework.response import Response

from classes.models import Classes
from invoices.models import Invoice
from payment_in_kind_Receipt.models import PIKReceipt
from receipts.models import Receipt
from students.models import Student
from students.serializers import StudentSerializer
from utils import SchoolIdMixin
from vouchers.models import Voucher


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

        day = request.GET.get('day')
        term = request.GET.get('term')
        month = request.GET.get('month')
        accountType = request.GET.get('accountType')
        range_start_date = request.GET.get('range_start_date')
        range_end_date = request.GET.get('range_end_date')
        week_start_date = request.GET.get('week_start_date')
        week_end_date = request.GET.get('week_end_date')
        filter_type = request.GET.get('filter_type') #day, term, month, range, week

        if not filter_type:
            return Response({'detail': f"Filter Type is required"}, status=status.HTTP_400_BAD_REQUEST)
        if filter_type == "range" and not range_start_date or not range_end_date:
            return Response({'detail': f"Both Start and End Date are required for range"}, status=status.HTTP_400_BAD_REQUEST)
        if filter_type == "month" and not month:
            return Response({'detail': f"Month is required"}, status=status.HTTP_400_BAD_REQUEST)
        if filter_type == "day" and not day:
            return Response({'detail': f"Day is required"}, status=status.HTTP_400_BAD_REQUEST)
        if filter_type == "term" and not term:
            return Response({'detail': f"Term is required"}, status=status.HTTP_400_BAD_REQUEST)
        if filter_type == "week" and not week_start_date or not week_end_date:
            return Response({'detail': f"Both week start and end date are required"}, status=status.HTTP_400_BAD_REQUEST)
        if not accountType:
            return Response({'detail': f"Account Type is required"}, status=status.HTTP_400_BAD_REQUEST)


        receiptsQuerySet = Receipt.objects.filter(
            school_id=school_id,
            is_reversed=False,
            account_type=accountType
        )
        pikQuerySet = PIKReceipt.objects.filter(
            school_id=school_id,
            is_posted=True,
            bank_account__account_type=accountType
        )
        expensesVouchers = Voucher.objects.filter(
            school_id=school_id,
            is_deleted=False,
            bank_account__account_type=accountType
        )
        invoicedAmountQuerySet = Invoice.objects.filter(
            school_id=school_id,
            term=term
        )

        receiptsQuerySet_aggregate = receiptsQuerySet.aggregate(result=Sum('totalAmount'))
        pikQuerySet_aggregate = pikQuerySet.aggregate(result=Sum('totalAmount'))
        expensesVouchers_aggregate = expensesVouchers.aggregate(result=Sum('totalAmount'))


        receipt_amount_sum = receiptsQuerySet_aggregate.get('result', Decimal('0.0')) if receiptsQuerySet_aggregate.get(
            'result') is not None else Decimal('0.0')
        pik_receipt_sum = pikQuerySet_aggregate.get('result', Decimal('0.0')) if pikQuerySet_aggregate.get(
            'result') is not None else Decimal('0.0')
        expensesVoucher_sum = expensesVouchers_aggregate.get('result', Decimal('0.0')) if expensesVouchers_aggregate.get(
            'result') is not None else Decimal('0.0')

        total_collections = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)
        total_vouchers = expensesVoucher_sum

        list_of_forms = Classes.objects.filter(school_id=school_id)

        for form in list_of_forms:
            form_name = form.classname

            receipts_query_set = copy(receiptsQuerySet)
            pik_query_set = copy(pikQuerySet)

            receipts_query_set = receipts_query_set.filter(student_class=form_name)
            pik_query_set = pik_query_set.filter(student_class=form_name)

            receipts_query_set_aggregate = receipts_query_set.aggregate(result=Sum('totalAmount'))
            pik_query_set_aggregate = pik_query_set.aggregate(result=Sum('totalAmount'))

            receipt_amount_sum = receipts_query_set_aggregate.get('result',Decimal('0.0')) if receipts_query_set_aggregate.get(
                'result') is not None else Decimal('0.0')
            pik_receipt_sum = pik_query_set_aggregate.get('result', Decimal('0.0')) if pik_query_set_aggregate.get(
                'result') is not None else Decimal('0.0')
            totalCollections = Decimal(receipt_amount_sum) + Decimal(pik_receipt_sum)


            invoicedAmountQuerySet_aggregate = invoicedAmountQuerySet.aggregate(result=Sum('amount'))
            invoiced_amount_sum = invoicedAmountQuerySet_aggregate.get('result',Decimal('0.0')) if invoicedAmountQuerySet_aggregate.get(
                'result') is not None else Decimal('0.0')


        return Response({"detail": "You"})