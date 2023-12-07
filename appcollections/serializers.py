from rest_framework import serializers

from account_types.serializers import AccountTypeSerializer
from bank_accounts.serializers import BankAccountSerializer
from currencies.serializers import CurrencySerializer
from payment_methods.serializers import PaymentMethodSerializer
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', required=False, read_only=True)
    votehead_details = VoteHeadSerializer(source='votehead', required=False, read_only=True)

    class Meta:
        model = Collection
        fields = '__all__'