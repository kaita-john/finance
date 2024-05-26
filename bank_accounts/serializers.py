from django.shortcuts import get_object_or_404
from rest_framework import serializers

from account_types.serializers import AccountTypeSerializer
from currencies.serializers import CurrencySerializer
from .models import BankAccount, AccountType, Currency


class BankAccountSerializer(serializers.ModelSerializer):
    account_type = serializers.UUIDField()
    currency = serializers.UUIDField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'GET':
            self.fields['account_type'] = AccountTypeSerializer(many=False)
            self.fields['currency'] = CurrencySerializer(many=False)

    def create(self, validated_data):
        account_type_data = validated_data.pop('account_type', None)
        if account_type_data:
            account_type = get_object_or_404(AccountType, id=account_type_data)
            validated_data['account_type'] = account_type

        currency_data = validated_data.pop('currency', None)
        if currency_data:
            currency = get_object_or_404(Currency, id=currency_data)
            validated_data['currency'] = currency

        return BankAccount.objects.create(**validated_data)


    class Meta:
        model = BankAccount
        fields = '__all__'
