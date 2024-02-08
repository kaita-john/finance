# Create your views here.

import uuid

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appcollections.models import Collection
from appcollections.serializers import CollectionSerializer
from constants import MANUAL, AUTO, PRIORITY, RATIO
from financial_years.models import FinancialYear
from invoices.models import Invoice
from reportss.models import trackBalance
from utils import SchoolIdMixin, IsAdminOrSuperUser, generate_unique_code, defaultCurrency, currentAcademicYear, \
    currentTerm, DefaultMixin
from voteheads.models import VoteHead, VoteheadConfiguration
from .models import Receipt
from .serializers import ReceiptSerializer


def manualCollection(self, request, school_id, current_financial_year):
    try:
        with transaction.atomic():
            receipt_no = generate_unique_code("RT")
            default_Currency = defaultCurrency(school_id)
            year = currentAcademicYear(school_id)
            term = currentTerm(school_id)
            if not default_Currency:
                Response({'detail': "Default Currency Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)
            if not year:
                Response({'detail': "Default Academic Year Not Set For This School"},
                         status=status.HTTP_400_BAD_REQUEST)
            if not term:
                Response({'detail': "Default Term Not Set For This School"}, status=status.HTTP_400_BAD_REQUEST)

            receipt_serializer = self.get_serializer(data=request.data)
            receipt_serializer.is_valid(raise_exception=True)
            receipt_serializer.validated_data['school_id'] = school_id
            receipt_serializer.validated_data['receipt_No'] = receipt_no
            receipt_serializer.validated_data['currency'] = default_Currency
            receipt_serializer.validated_data['term'] = term
            receipt_serializer.validated_data['year'] = year

            receipt_serializer.validated_data.pop('collections_values', [])

            trackBalance(
                receipt_serializer.validated_data['student'],
                school_id,
                receipt_serializer.validated_data['totalAmount'],
                "plus",
                term,
                year
            )

            receipt_instance = receipt_serializer.save()
            receipt_instance.student_class = receipt_instance.student.current_Class
            receipt_instance.financial_year = current_financial_year
            receipt_instance.save()


            collections_data = request.data.get('collections_values', [])

            sum_Invoice_Amount = 0
            overpayment = 0

            if not collections_data:
                overpayment += receipt_instance.totalAmount
            if collections_data:
                for collection_data in collections_data:
                    collection_data['receipt'] = receipt_instance.id
                    collection_data['school_id'] = school_id
                    collection_data['student'] = receipt_instance.student.id
                    collection_serializer = CollectionSerializer(data=collection_data)
                    collection_serializer.is_valid(raise_exception=True)
                    created_collection = collection_serializer.save()

                    votehead_instance = created_collection.votehead
                    term_instance = created_collection.receipt.term
                    year_instance = created_collection.receipt.year
                    student = created_collection.receipt.student

                    try:
                        invoice_instance = Invoice.objects.get(votehead=votehead_instance, term=term_instance, year=year_instance, school_id=school_id, student=student)

                        if (invoice_instance.paid + created_collection.amount) > invoice_instance.amount:
                            raise ValueError("Transaction 1 cancelled: Total paid amount exceeds total invoice amount")
                        else:
                            sum_Invoice_Amount += invoice_instance.amount

                    except Invoice.DoesNotExist:
                        print("Invoice does not exist")
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")


            if receipt_instance.totalAmount > sum_Invoice_Amount:

                overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True, school_id=school_id).first()
                if not overpayment_votehead:
                    raise ValueError("No VoteHead found with is_Overpayment_Default set to true")
                overpayment += sum_Invoice_Amount - receipt_instance.totalAmount

            if overpayment > 0:
                newCollection = Collection(
                    student=receipt_instance.student,
                    receipt=receipt_instance,
                    amount=Decimal(overpayment),
                    votehead=overpayment_votehead,
                    school_id=receipt_instance.school_id,
                    is_overpayment = True
                )
                newCollection.save()

            print("Here")
            bank_account = receipt_instance.bank_account
            amount = receipt_instance.totalAmount
            initial_balance = bank_account.balance
            new_balance = initial_balance + Decimal(amount)
            bank_account.balance = new_balance
            bank_account.save()


        return Response({'detail': 'Receipt and collections created successfully'}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)






def autoCollection(self, request, school_id, auto_configuration_type, current_financial_year):
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

            receipt_serializer = self.get_serializer(data=request.data)
            receipt_serializer.is_valid(raise_exception=True)

            receipt_serializer.validated_data['school_id'] = school_id
            receipt_serializer.validated_data['receipt_No'] = receipt_no
            receipt_serializer.validated_data['currency'] = default_Currency
            receipt_serializer.validated_data['term'] = term
            receipt_serializer.validated_data['year'] = year
            receipt_serializer.validated_data.pop('collections_values', [])

            trackBalance(
                receipt_serializer.validated_data['student'],
                school_id,
                receipt_serializer.validated_data['totalAmount'],
                "plus",
                term,
                year
            )
            receipt_instance = receipt_serializer.save()


            receipt_instance.student_class = receipt_instance.student.current_Class
            receipt_instance.financial_year = current_financial_year
            receipt_instance.financial_year = current_financial_year
            receipt_instance.save()

            overpayment = 0

            totalAmount = receipt_instance.totalAmount
            student = receipt_instance.student
            voteheads = Invoice.objects.filter( term=term, year=year, school_id=school_id, student=student)

            if not voteheads:
                overpayment += totalAmount

            else:
                votehead_ids = voteheads.values('votehead').distinct()
                votehead_objects = VoteHead.objects.filter(id__in=votehead_ids)
                numberOfVoteheads = len(votehead_objects)

                if auto_configuration_type == RATIO:
                    eachVoteheadWillGet = totalAmount / numberOfVoteheads
                    for votehead in votehead_objects:
                        try:
                            invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=year, school_id=school_id, student=student)
                            if (invoice_instance.paid + eachVoteheadWillGet) > invoice_instance.amount:
                                amountRequired = invoice_instance.amount - invoice_instance.paid

                                collection_data = {'student': student.id,'receipt': receipt_instance.id,'amount': amountRequired,'votehead': votehead.id,'school_id': school_id,}
                                collection_serializer = CollectionSerializer(data=collection_data)
                                collection_serializer.is_valid(raise_exception=True)
                                collection_serializer.save()

                                balance = eachVoteheadWillGet - amountRequired
                                print(f"balance is {balance}")
                                if balance > 0:
                                    overpayment = overpayment + balance

                            else:

                                collection_data = {
                                    'student': student.id,
                                    'receipt': receipt_instance.id,
                                    'amount': eachVoteheadWillGet,
                                    'votehead': votehead.id,
                                    'school_id': school_id,
                                }

                                collection_serializer = CollectionSerializer(data=collection_data)
                                collection_serializer.is_valid(raise_exception=True)
                                collection_serializer.save()

                        except Invoice.DoesNotExist:
                            pass
                        except Invoice.MultipleObjectsReturned:
                            raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                if auto_configuration_type == PRIORITY:
                    distinct_voteheads = Invoice.objects.filter(term=term, year=year, school_id=school_id, student=student) \
                        .values_list('votehead', flat=True) \
                        .distinct()
                    ordered_voteheads = VoteHead.objects.filter(id__in=distinct_voteheads) \
                        .order_by(F('priority_number').asc(nulls_first=True))


                    for index, votehead in enumerate(ordered_voteheads):
                        print(f"Votehead -> {votehead}, Priority -> {votehead.priority_number}")
                        if not votehead.is_Overpayment_Default:
                            if totalAmount > 0:
                                try:
                                    invoice_instance = Invoice.objects.get(votehead=votehead, term=term, year=year, school_id=school_id, student=student)

                                    if (invoice_instance.paid + totalAmount) > invoice_instance.amount:
                                        amountRequired = invoice_instance.amount - invoice_instance.paid

                                        collection_data = {
                                            'student': student.id,
                                            'receipt': receipt_instance.id,
                                            'amount': amountRequired,
                                            'votehead': votehead.id,
                                            'school_id': school_id,
                                        }

                                        collection_serializer = CollectionSerializer(data=collection_data)
                                        collection_serializer.is_valid(raise_exception=True)
                                        collection_serializer.save()

                                        totalAmount = totalAmount - amountRequired

                                        if index == len(voteheads) - 1:
                                            if totalAmount > 0:
                                                overpayment = overpayment + totalAmount

                                    else:
                                        collectionAmount = totalAmount
                                        collection = Collection(student = student,receipt=receipt_instance,amount=collectionAmount,votehead=votehead,school_id=school_id)
                                        collection.save()

                                        totalAmount = 0.00

                                except Invoice.DoesNotExist:
                                    pass
                                except Invoice.MultipleObjectsReturned:
                                    raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

            if overpayment > 0:
                overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True, school_id=school_id).first()
                if not overpayment_votehead:
                    raise ValueError("Overpayment votehead has not been configured")

                newCollection = Collection(
                    student=receipt_instance.student,
                    receipt=receipt_instance,
                    amount=overpayment,
                    votehead=overpayment_votehead,
                    school_id=receipt_instance.school_id,
                    is_overpayment = True
                )
                newCollection.save()

            print("Here")
            bank_account = receipt_instance.bank_account
            amount = receipt_instance.totalAmount
            initial_balance = bank_account.balance
            new_balance = initial_balance + Decimal(amount)
            bank_account.balance = new_balance
            bank_account.save()


        return Response({'detail': 'Receipt and collections created successfully'}, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReceiptCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        try:
            current_financial_year = FinancialYear.objects.get(is_current=True, school=school_id)
        except ObjectDoesNotExist:
            return Response({'detail': f"Current Financial Year not set"}, status=status.HTTP_400_BAD_REQUEST)

        print("Print here")

        try:
            configuration = VoteheadConfiguration.objects.get(school_id=school_id)
        except ObjectDoesNotExist:
            return Response({'detail': "Please set up votehead configuration for this school first!"}, status=status.HTTP_400_BAD_REQUEST)

        configuration_type = configuration.configuration_type
        auto_configuration_type = configuration.auto_configuration_type

        if configuration_type == MANUAL:
            return manualCollection(self, request, school_id, current_financial_year)

        elif configuration_type == AUTO:

            return autoCollection(self, request, school_id, auto_configuration_type, current_financial_year)




class ReceiptListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Receipt.objects.none()
        self.check_defaults(self.request, school_id)

        queryset = Receipt.objects.filter(school_id=school_id)

        is_reversed_param = self.request.query_params.get('reversed', None)
        if is_reversed_param is not None and is_reversed_param != "" and is_reversed_param != "null":
            queryset = queryset.filter(is_reversed=True)
            print("It is reversed")
        else:
            queryset = queryset.filter(is_reversed=False)
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




class ReceiptDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = uuid.UUID(primarykey)
            return Receipt.objects.get(id=id)
        except (ValueError, Receipt.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.is_reversed:
            return Response({'detail': "You cannot update a reversed receipt"},status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id
            self.perform_update(serializer)
            return Response({'detail': 'Receipt updated successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = instance.school_id
        term = instance.term
        year = instance.year

        if instance.is_reversed:
            return Response({'detail': "This receipt is already reversed"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                instance.is_reversed = True
                instance.reversal_date = timezone.now()
                instance.save()

                bank_account = instance.bank_account
                previous_receipt_amount = instance.totalAmount
                current_balance = bank_account.balance #Bank balance as it stands
                new_balance = current_balance - Decimal(previous_receipt_amount)
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

            return Response({'detail': "Receipt Reversed Successfully"}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
