from rest_framework import serializers

from account_types.serializers import AccountTypeSerializer
from appcollections.models import Collection
from appcollections.serializers import CollectionSerializer
from bank_accounts.serializers import BankAccountSerializer
from currencies.serializers import CurrencySerializer
from payment_methods.serializers import PaymentMethodSerializer
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    student_Details = StudentSerializer(source='student', required=False, read_only=True)
    collections_values = serializers.ListField(child=serializers.DictField(), allow_null=True, allow_empty=True, write_only=True)
    account_type_Details = AccountTypeSerializer(source='account_type', required=False, read_only=True)
    bank_account_Details = BankAccountSerializer(source='bank_account', required=False, read_only=True)
    payment_method_Details = PaymentMethodSerializer(source='payment_method', required=False, read_only=True)
    currency_Details = CurrencySerializer(source='currency', required=False, read_only=True)
    related_collections = serializers.SerializerMethodField(read_only=True)


    class Meta:
        model = Receipt
        fields = '__all__'

    def get_related_collections(self, instance):
        collections = Collection.objects.filter(receipt = instance)
        collection_serializer = CollectionSerializer(collections, many=True)
        return collection_serializer.data



class AutoReceiptSerializer(serializers.ModelSerializer):
    student_Details = StudentSerializer(source='student', required=False, read_only=True)
    collections_values = serializers.ListField(child=serializers.DictField(), allow_null=True, write_only=True)
    account_type_Details = AccountTypeSerializer(source='account_type', required=False, read_only=True)
    bank_account_Details = BankAccountSerializer(source='bank_account', required=False, read_only=True)
    payment_method_Details = PaymentMethodSerializer(source='payment_method', required=False, read_only=True)
    currency_Details = CurrencySerializer(source='currency', required=False, read_only=True)

    class Meta:
        model = Receipt
        fields = '__all__'