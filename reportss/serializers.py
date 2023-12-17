from rest_framework import serializers

from reportss.models import ReportStudentBalance, StudentTransactionsPrintView


class ReportStudentBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStudentBalance
        fields = '__all__'


class StudentTransactionsPrintViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentTransactionsPrintView
        fields = '__all__'
