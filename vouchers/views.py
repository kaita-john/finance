# Create your views here.
from datetime import datetime

from _decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from financial_years.models import FinancialYear
from utils import SchoolIdMixin, IsAdminOrSuperUser, UUID_from_PrimaryKey, DefaultMixin
from voucher_attachments.models import VoucherAttachment
from voucher_attachments.serializers import Voucherattachmentserializer
from voucher_items.models import VoucherItem
from voucher_items.serializers import VoucherItemSerializer
from .models import Voucher
from .serializers import VoucherSerializer


class VoucherCreateView(SchoolIdMixin, DefaultMixin, generics.CreateAPIView):
    serializer_class = VoucherSerializer
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

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            recipientType = serializer.validated_data.get('recipientType')
            if not recipientType:
                return Response({'detail': f"Recipient type is a must"}, status=status.HTTP_400_BAD_REQUEST)

            if recipientType == "staff":
                if not serializer.validated_data.get('staff'):
                    return Response({'detail': f"Staff is a must"}, status=status.HTTP_400_BAD_REQUEST)

            if recipientType == "supplier":
                if not serializer.validated_data.get('supplier'):
                    return Response({'detail': f"Supplier is a must"}, status=status.HTTP_400_BAD_REQUEST)

            if recipientType == "other":
                if not serializer.validated_data.get('other'):
                    return Response({'detail': f"Other is a must"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                with transaction.atomic():

                    payment_items_data = serializer.validated_data.pop('payment_values', [])
                    attachments_values = serializer.validated_data.get('attachments_values')

                    if attachments_values:
                        attachments_data = serializer.validated_data.pop('attachments_values', [])

                    voucher = serializer.save()

                    voucher.financial_year = current_financial_year
                    voucher.save()

                    bank_account = voucher.bank_account
                    amount = voucher.totalAmount
                    initial_balance = bank_account.balance
                    new_balance = initial_balance - Decimal(amount)
                    bank_account.balance = new_balance
                    bank_account.save()

                    for payment_item_data in payment_items_data:
                        payment_item_data['school_id'] = voucher.school_id
                        payment_item_data['voucher'] = voucher.id
                        print(f"checking -> {payment_item_data}")
                        payment_item_serializer = VoucherItemSerializer(data=payment_item_data)
                        payment_item_serializer.is_valid(raise_exception=True)
                        print(f"checking -> {payment_item_serializer.validated_data}")
                        payment_item_serializer.save()

                    if attachments_values:
                        for attachment in attachments_data:
                            attachment['school_id'] = voucher.school_id
                            attachment['voucher'] = voucher.id
                            voucherattachmentserializer = Voucherattachmentserializer(data=attachment)
                            voucherattachmentserializer.is_valid(raise_exception=True)
                            voucherattachmentserializer.save()

                    return Response({'detail': f'Voucher created successfully'},status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print("Here")
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class VoucherListView(SchoolIdMixin, DefaultMixin, generics.ListAPIView):
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]
    pagination_class = PageNumberPagination


    def get_queryset(self):
        school_id = self.check_school_id(self.request)
        if not school_id:
            return Voucher.objects.none()
        self.check_defaults(self.request, school_id)
        queryset = Voucher.objects.filter(school_id=school_id, is_deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return JsonResponse([], safe=False,status=200)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)



class VoucherDetailView(SchoolIdMixin, DefaultMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSuperUser]

    def get_object(self):
        primarykey = self.kwargs['pk']
        try:
            id = UUID_from_PrimaryKey(primarykey)
            return Voucher.objects.get(id=id)
        except (ValueError, Voucher.DoesNotExist):
            raise NotFound({'detail': 'Record Not Found'})

    def update(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'detail': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.validated_data['school_id'] = school_id

            try:
                with transaction.atomic():
                    VoucherItem.objects.filter(voucher=instance).delete()
                    VoucherAttachment.objects.filter(voucher=instance).delete()

                    current_financial_year = FinancialYear.objects.get(is_current=True, school=school_id)
                    serializer.validated_data['financial_year'] = current_financial_year
                    voucher = serializer.save()

                    bank_account = voucher.bank_account
                    initial_voucher_amount = instance.totalAmount
                    initial_balance = bank_account.balance
                    if initial_voucher_amount is not None:
                        initial_balance += Decimal(initial_voucher_amount)
                    new_voucher_amount = voucher.totalAmount
                    new_balance = initial_balance - Decimal(new_voucher_amount)
                    bank_account.balance = new_balance
                    bank_account.save()

                    # Save payment items
                    payment_items_data = serializer.validated_data.get('payment_values', [])
                    for payment_item_data in payment_items_data:
                        payment_item_data['school_id'] = school_id
                        payment_item_data['voucher'] = voucher.id
                        payment_item_serializer = VoucherItemSerializer(data=payment_item_data)
                        payment_item_serializer.is_valid(raise_exception=True)
                        payment_item_serializer.save()

                    # Save attachments
                    attachments_data = serializer.validated_data.get('attachments_values', [])
                    for attachment_data in attachments_data:
                        attachment_data['school_id'] = school_id
                        attachment_data['voucher'] = voucher.id
                        attachment_serializer = Voucherattachmentserializer(data=attachment_data)
                        attachment_serializer.is_valid(raise_exception=True)
                        attachment_serializer.save()

                    return Response({'detail': 'Voucher updated successfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()

    def delete(self, request, *args, **kwargs):
        school_id = self.check_school_id(request)
        if not school_id:
            return JsonResponse({'error': 'Invalid school_id in token'}, status=401)
        self.check_defaults(self.request, school_id)

        voucher = self.get_object()

        if voucher.is_deleted:
            return Response({'detail': f"This Voucher is already deleted"}, status=status.HTTP_400_BAD_REQUEST)

        voucher.is_deleted = True
        voucher.date_deleted = datetime.now()
        voucher.save()

        bank_account = voucher.bank_account
        amount = voucher.totalAmount
        initial_balance = bank_account.balance
        new_balance = initial_balance + Decimal(amount)
        bank_account.balance = new_balance
        bank_account.save()


        return Response({'detail': 'Voucher deleted successfully!'}, status=status.HTTP_200_OK)