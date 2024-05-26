from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from bank_accounts.serializers import BankAccountSerializer
from currencies.serializers import CurrencySerializer
from payment_methods.serializers import PaymentMethodSerializer
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from vouchers.models import Voucher
from vouchers.serializers import VoucherSerializer
from .models import PIKReceipt


class PIKReceiptSerializer(serializers.ModelSerializer):
    student_Details = StudentSerializer(source='student', required=False, read_only=True)
    pik_values = serializers.ListField(child=serializers.DictField(), write_only=True)
    bank_account_Details = BankAccountSerializer(source='bank_account', required=False, read_only=True)
    payment_method_Details = PaymentMethodSerializer(source='payment_method', required=False, read_only=True)
    currency_Details = CurrencySerializer(source='currency', required=False, read_only=True)
    votehead_Details = VoteHeadSerializer(source='votehead', required=False, read_only=True)
    payment_in_kinds = serializers.SerializerMethodField(read_only=True)

    related_voucher = serializers.SerializerMethodField(read_only=True)

    def get_related_voucher(self, obj):
        receipt_instance_id = obj.id
        try:
            related_voucher = Voucher.objects.get(referallNumber=receipt_instance_id)
            related_voucher.is_deleted = True
            serializer = VoucherSerializer(related_voucher)
            return serializer.data
        except ObjectDoesNotExist:
            return {}

    def get_payment_in_kinds(self, obj):
        from payment_in_kinds.serializers import PaymentInKindSerializer_Limited
        payment_in_kinds = obj.paymentinkinds.filter(receipt=obj)
        return PaymentInKindSerializer_Limited(payment_in_kinds, many=True).data

    class Meta:
        model = PIKReceipt
        fields = '__all__'


