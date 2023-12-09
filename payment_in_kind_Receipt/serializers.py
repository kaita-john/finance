from rest_framework import serializers

from bank_accounts.serializers import BankAccountSerializer
from currencies.serializers import CurrencySerializer
from payment_methods.serializers import PaymentMethodSerializer
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import PIKReceipt


class PIKReceiptSerializer(serializers.ModelSerializer):
    student_Details = StudentSerializer(source='student', required=False, read_only=True)
    pik_values = serializers.ListField(child=serializers.DictField(), write_only=True)
    bank_account_Details = BankAccountSerializer(source='bank_account', required=False, read_only=True)
    payment_method_Details = PaymentMethodSerializer(source='payment_method', required=False, read_only=True)
    currency_Details = CurrencySerializer(source='currency', required=False, read_only=True)
    votehead_Details = VoteHeadSerializer(source='votehead', required=False, read_only=True)

    class Meta:
        model = PIKReceipt
        fields = '__all__'