from django.db import models
from rest_framework import serializers

from account_types.serializers import AccountTypeSerializer
from financial_years.models import FinancialYear
from financial_years.serializers import FinancialYearSerializer
from voteheads.models import VoteHead
from voteheads.serializers import VoteHeadSerializer
from .models import Budget


class BudgetItem(models.Model):
    votehead_id = models.UUIDField(max_length=255)
    expenditure_amount = models.DecimalField(max_digits=10, decimal_places=2)
    income_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.votehead_id}"

class BudgetItemSerializer(serializers.ModelSerializer):
    votehead_details = serializers.SerializerMethodField()

    class Meta:
        model = BudgetItem
        fields = '__all__'

    def get_votehead_details(self, obj):
        votehead_id = obj.get('votehead_id', None)
        if votehead_id:
            try:
                votehead = VoteHead.objects.get(id=votehead_id)
                votehead_serializer = VoteHeadSerializer(votehead)
                return votehead_serializer.data
            except VoteHead.DoesNotExist:
                return None
        else:
            return None




class BudgetSerializer(serializers.ModelSerializer):
    accountType_details = AccountTypeSerializer(source='accountType', required=False, read_only=True)
    financialYear_details = FinancialYearSerializer(source='financialYear', required=False, read_only=True)
    budget_items = BudgetItemSerializer(many=True, read_only=True)

    class Meta:
        model = Budget
        fields = '__all__'






