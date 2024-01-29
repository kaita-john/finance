# Create your views here.

import uuid
from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from account_types.models import AccountType
from appcollections.models import Collection
from financial_years.models import FinancialYear
from invoices.models import Invoice
from payment_in_kinds.serializers import PaymentInKindSerializer
from receipts.models import Receipt
from reportss.models import trackBalance
from utils import SchoolIdMixin, IsAdminOrSuperUser, generate_unique_code, defaultCurrency, currentAcademicYear, \
    currentTerm
from voteheads.models import VoteHead
from .models import PIKReceipt
from .serializers import PIKReceiptSerializer


class PIKReceiptCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            current_financial_year = FinancialYear.objects.get(is_current=True, school=school_id)
        except ObjectDoesNotExist:
            return Response({'detail': f"Current Financial Year not set"}, status=status.HTTP_400_BAD_REQUEST)


        try:
            with transaction.atomic():
                receipt_no = generate_unique_code("RT")
                default_Currency = defaultCurrency(school_id)
                year = currentAcademicYear(school_id)
                term = currentTerm(school_id)
                if not default_Currency:
                    Response({'detail': "Default Currency Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
                if not year:
                    Response({'detail': "Default Academic Year Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
                if not term:
                    Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

                totalAmount = 0.00
                pik_values = request.data.get('pik_values', [])
                if pik_values:
                    totalAmount = sum( Decimal(item['unit_cost']) * Decimal(item['quantity']) for item in pik_values)

                pikreceipt_serializer = self.get_serializer(data=request.data)
                pikreceipt_serializer.is_valid(raise_exception=True)
                pikreceipt_serializer.validated_data['school_id'] = school_id
                pikreceipt_serializer.validated_data['receipt_No'] = receipt_no
                pikreceipt_serializer.validated_data['currency'] = default_Currency
                pikreceipt_serializer.validated_data['term'] = term
                pikreceipt_serializer.validated_data['year'] = year
                pikreceipt_serializer.validated_data['totalAmount'] = totalAmount
                pikreceipt_serializer.validated_data.pop('pik_values', [])

                trackBalance(
                    pikreceipt_serializer.validated_data['student'],
                    school_id,
                    pikreceipt_serializer.validated_data['totalAmount'],
                    "plus",
                    term,
                    year
                )
                pikreceipt_instance = pikreceipt_serializer.save()

                pikreceipt_instance.student_class = pikreceipt_instance.student.current_Class
                pikreceipt_instance.financial_year = current_financial_year
                pikreceipt_instance.save()

                overpayment = 0
                overpayment_amount = pikreceipt_serializer.validated_data.get('overpayment_amount')

                if overpayment_amount:
                    overpayment=overpayment_amount

                for value in pik_values:
                    value['receipt'] = pikreceipt_instance.id
                    value['school_id'] = school_id
                    value['student'] = pikreceipt_instance.student.id
                    value['amount'] = value['quantity'] * value['unit_cost']
                    paymentInKind_serializer = PaymentInKindSerializer(data=value)
                    paymentInKind_serializer.is_valid(raise_exception=True)
                    created_Pik = paymentInKind_serializer.save()

                    print(f"Votehead is {value['votehead']}")
                    print(f"Votehead is {value['votehead']}")
                    print(f"Votehead is {value['votehead']}")

                    term_instance = created_Pik.receipt.term
                    year_instance = created_Pik.receipt.year
                    student = created_Pik.receipt.student

                    try:
                        invoice_instance = Invoice.objects.get(votehead__id=value['votehead'], term=term_instance,year=year_instance, school_id=school_id, student=student)

                        requiredAmount = invoice_instance.amount - invoice_instance.paid
                        if created_Pik.amount > requiredAmount:
                            raise ValueError(f"Amount entered is more than required balance for votehead {invoice_instance.votehead.vote_head_name}")

                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                if  overpayment > 0:

                    overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True).first()
                    if not overpayment_votehead:
                        raise ValueError("No VoteHead found with is_Overpayment_Default set to true")

                    try:
                        defaultAccountType = AccountType.objects.get(school = school_id, is_default=True)
                    except ObjectDoesNotExist:
                        raise ValueError("Default Account Type Not Set")



                    receiptInstance = Receipt.objects.create(
                        school_id = school_id,
                        student = student,
                        receipt_No = generate_unique_code("REC"),
                        totalAmount = overpayment,
                        account_type = defaultAccountType,
                        bank_account=pikreceipt_instance.bank_account,
                        payment_method=None,
                        term=term,
                        year=year,
                        currency=default_Currency,
                        transaction_code=generate_unique_code("TRN"),
                        transaction_date=datetime.now(),
                        addition_notes="Payment In Kind Receipt",
                        student_class=student.current_Class,
                    )

                    trackBalance(
                        student,
                        school_id,
                        overpayment,
                        "plus",
                        term,
                        year
                    )

                    receiptInstance.save()

                    newCollection = Collection(
                        student=student,
                        receipt=receiptInstance,
                        amount=overpayment,
                        votehead=overpayment_votehead,
                        school_id=school_id,
                        is_overpayment=True
                    )
                    newCollection.save()
                    print(f"Overpayment is there")


                else:
                    print(f"It is not greater than - No overpayment")

                print("Here  1")
                bank_account = pikreceipt_instance.bank_account
                amount = pikreceipt_instance.totalAmount
                initial_balance = bank_account.balance
                new_balance = initial_balance + Decimal(amount)
                bank_account.balance = new_balance
                bank_account.save()


        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Records created successfully'}, status=status.HTTP_201_CREATED)



class PIKReceiptListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return PIKReceipt.objects.none()
        queryset = PIKReceipt.objects.filter(school_id=school_id)

        is_posted = self.request.query_params.get('posted', None)
        if is_posted is not None:
            if is_posted:
                queryset = queryset.filter(is_posted=True)
            if not is_posted:
                queryset = queryset.filter(is_posted=False)
        else:
            queryset = queryset
            print("It is not reversed")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False, status=200)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)




class PIKReceiptDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = PIKReceipt.objects.all()
    serializer_class = PIKReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = uuid.UUID(primarykey)
            return PIKReceipt.objects.get(id=id)
        except (ValueError, PIKReceipt.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if not instance.is_posted:
            return Response({'detail': "You cannot update this record"},status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_update(serializer)
            return Response({'detail': 'PIKReceipt updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if not instance.is_posted:
            return Response({'detail': "Item is already unposted"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                instance.is_posted = False
                instance.unposted_date = timezone.now()
                instance.save()

                # Subtract the receipt amount from the bank account
                bank_account = instance.bank_account
                amount = instance.totalAmount
                initial_balance = bank_account.balance
                new_balance = initial_balance - Decimal(amount)
                bank_account.balance = new_balance
                bank_account.save()

                receipt_instance = instance
                trackBalance(
                    receipt_instance.student,
                    receipt_instance.school_id,
                    receipt_instance.totalAmount,
                    "minus",
                    receipt_instance.term,
                    receipt_instance.year
                )

            return Response({'detail': "PIKReceipt Reversed Successfully"}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
