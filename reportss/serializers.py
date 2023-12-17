from rest_framework import serializers

from reportss.models import ReportStudentBalance


class ReportStudentBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStudentBalance
        fields = '__all__'
