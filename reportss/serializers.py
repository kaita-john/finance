from rest_framework import serializers

from reportss.models import ReportStudentBalance, StudentTransactionsPrintView, IncomeSummary


class ReportStudentBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStudentBalance
        fields = '__all__'


class StudentTransactionsPrintViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentTransactionsPrintView
        fields = '__all__'


class IncomeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeSummary
        fields = '__all__'
