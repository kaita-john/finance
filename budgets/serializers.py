from rest_framework import serializers

from account_types.serializers import AccountTypeSerializer
from financial_years.models import FinancialYear
from financial_years.serializers import FinancialYearSerializer
from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    accountType_details = AccountTypeSerializer(source='accountType', required=False, read_only=True)
    financialYear_details = FinancialYearSerializer(source='financialYear', required=False, read_only=True)
    class Meta:
        model = Budget
        fields = '__all__'


