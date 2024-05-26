from django.http import HttpResponse
from rest_framework import serializers

from invoices.models import Invoice
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import PaymentInKind


class PaymentInKindSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', required=False, read_only=True)
    votehead_details = VoteHeadSerializer(source='votehead', required=False, read_only=True)
    unallocated = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PaymentInKind
        fields = '__all__'

    def get_unallocated(self, obj):
        collection = obj
        receipt = collection.receipt

        votehead = collection.votehead
        year = receipt.year
        term = receipt.term
        school_uuid = receipt.school_id

        try:
            amount_query = Invoice.objects.filter(
                school_id=school_uuid,
                term=term,
                year=year,
                votehead=votehead
            ).first()

            if amount_query is not None:
                amount = amount_query.paid
            else:
                print(f"Amount query is none")
                amount = 0.00

            return str(amount)

        except Exception as exception:
            HttpResponse(f"Bad Request {exception}")





class PaymentInKindSerializer_Limited(serializers.ModelSerializer):
    vote_head_name = serializers.CharField(source='votehead.vote_head_name', read_only=True)
    class Meta:
        model = PaymentInKind
        fields = ['id', 'vote_head_name', 'amount']

