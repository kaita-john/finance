# Create your views here.

import uuid

from django.db import transaction
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
from invoices.models import Invoice
from utils import SchoolIdMixin, IsAdminOrSuperUser, generate_unique_code
from voteheads.models import VoteHead
from .models import Receipt
from .serializers import ReceiptSerializer


class ReceiptCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)

        try:
            with transaction.atomic():
                receipt_no = generate_unique_code("RT")

                receipt_serializer = self.get_serializer(data=request.data)
                receipt_serializer.is_valid(raise_exception=True)
                receipt_serializer.validated_data['school_id'] = school_id
                receipt_serializer.validated_data['receipt_No'] = receipt_no
                receipt_serializer.validated_data.pop('collections_values', [])
                receipt_instance = receipt_serializer.save()

                print("Created Receipt")

                collections_data = request.data.get('collections_values', [])

                sum_Invoice_Amount = 0
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
                        invoice_instance = Invoice.objects.get(votehead=votehead_instance, term=term_instance,year=year_instance, school_id=school_id, student=student)

                        if (invoice_instance.paid + created_collection.amount) > invoice_instance.amount:
                            raise ValueError("Transaction 1 cancelled: Total paid amount exceeds total invoice amount")
                        else:
                            invoice_instance.paid += created_collection.amount
                            invoice_instance.due = invoice_instance.amount - invoice_instance.paid
                            invoice_instance.save()

                            sum_Invoice_Amount += invoice_instance.amount

                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

                if receipt_instance.totalAmount > sum_Invoice_Amount:

                    overpayment_votehead = VoteHead.objects.filter(is_Overpayment_Default=True).first()
                    if not overpayment_votehead:
                        raise ValueError("No VoteHead found with is_Overpayment_Default set to true")

                    overpayment_Amount = sum_Invoice_Amount - receipt_instance.totalAmount
                    newCollection = Collection(
                        student=receipt_instance.student,
                        receipt=receipt_instance,
                        amount=overpayment_Amount,
                        votehead=overpayment_votehead,
                        school_id=receipt_instance.school_id
                    )
                    newCollection.save()

                    try:
                        invoice_instance = Invoice.objects.get(votehead=overpayment_votehead, term=term_instance,
                                                               year=year_instance, school_id=school_id, student=student)

                        if (invoice_instance.paid + created_collection.amount) > invoice_instance.amount:
                            raise ValueError("Transaction 2 cancelled: Total paid amount exceeds total invoice amount")
                        else:
                            invoice_instance.paid += created_collection.amount
                            invoice_instance.due = invoice_instance.amount - invoice_instance.paid
                            invoice_instance.save()

                            sum_Invoice_Amount += invoice_instance.amount
                    except Invoice.DoesNotExist:
                        pass
                    except Invoice.MultipleObjectsReturned:
                        raise ValueError("Transaction cancelled: Multiple invoices found for the given criteria")

        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Receipt and collections created successfully'}, status=status.HTTP_201_CREATED)



class ReceiptListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Receipt.objects.none()
        queryset = Receipt.objects.filter(school_id=school_id)

        overpayment = self.request.query_params.get('overpayment', None)
        if overpayment is not None:
            queryset = Receipt.objects.filter(school_id=school_id)

        is_reversed_param = self.request.query_params.get('reversed', None)
        if is_reversed_param is not None:
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




class ReceiptDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
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

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
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
            Response({'detail': "This invoice is already reversed"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                collections = Collection.objects.filter(receipt=instance).all()
                for collection in collections:
                    collected_amount = collection.amount
                    votehead = collection.votehead
                    invoicelist = Invoice.objects.filter(school_id=school_id, term=term, year=year,votehead=votehead).all()
                    for invoice in invoicelist:
                        invoice.paid -= collected_amount
                        invoice.due += collected_amount
                        invoice.save()

                instance.is_reversed = True
                instance.reversal_date = timezone.now()
                instance.save()

            return Response({'detail': "Receipt Reversed Successfully"}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
