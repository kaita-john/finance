import requests
from _decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from finance import settings
from receipts.views import ReceiptCreateView
from utils import SchoolIdMixin, UUID_from_PrimaryKey, DefaultMixin, defaultAccountType, defaultBankAccount, \
    default_MpesaPaymentMethod, IsAdminOrSuperUser
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionCreateView(SchoolIdMixin, generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school in token'}, status=401)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['school'] = school_id
            self.perform_create(serializer)
            return Response({'detail': 'Transaction created successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class TransactionListView(SchoolIdMixin, generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Transaction.objects.none()
        queryset = Transaction.objects.filter(school_id=school_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse({}, status=200)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)


class TransactionDetailView(SchoolIdMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Transaction.objects.get(id=id)
        except (ValueError, Transaction.DoesNotExist):
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
            return Response({'detail': 'Transaction updated successfully'}, status=status.HTTP_201_CREATED)
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






class SettleTransactionView(SchoolIdMixin, DefaultMixin, generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        with transaction.atomic():
            try:
                transid = instance.transid
                timestamp = instance.timestamp
                amount = instance.amount
                student = instance.student

                getdefaultAccountType = defaultAccountType(school_id)
                getdefaultBankAccount = defaultBankAccount(school_id)
                getdefaultIntegrationPaymentMethod = default_MpesaPaymentMethod(school_id)


                data = {
                    "student": student.id,
                    "totalAmount": Decimal(amount),
                    "account_type": getdefaultAccountType,
                    "bank_account": getdefaultBankAccount,
                    "payment_method": getdefaultIntegrationPaymentMethod,
                    "addition_notes": "SETTLEMENT",
                    "transaction_code": transid,
                    "transaction_date": timestamp,
                }

                view_name = 'receipt-create'
                receipt_create_url = request.build_absolute_uri(reverse("receipts:receipt-create"))
                response = requests.post(receipt_create_url, json=data)

                if response.status_code == 201:
                    instance.status = "COMPLETE"
                    instance.save()
                    return Response({'detail': 'Record deleted successfully and Receipt created'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Error creating Receipt'}, status=response.status_code)
            except Exception as exception:
                return Response({'detail': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
