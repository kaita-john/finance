from rest_framework import serializers

from bank_accounts.serializers import BankAccountSerializer
from payment_methods.serializers import PaymentMethodSerializer
from school.serializer import SchoolSerializer
from term.serializers import TermSerializer
from .models import Bursary


class BursarySerializer(serializers.ModelSerializer):
    bankAccount_details = BankAccountSerializer(source='bankAccount', required=False, read_only=True, many=False)
    paymentMethod_details = PaymentMethodSerializer(source='paymentMethod', allow_null=True, required=False, read_only=True, many=False)
    term_details = TermSerializer(source='term',required=False, read_only=True, many=False)
    school_details = SchoolSerializer(source='school',required=False, read_only=True, many=False)
    items_list = serializers.ListField(child=serializers.DictField(), allow_null=True, required=False, write_only=True)
    items = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Bursary
        fields = '__all__'

    def get_items(self, obj):
        from items.serializers import ItemSerializer
        try:
            items = obj.items.all()
        except AttributeError:
            items = []
        return ItemSerializer(items, many=True).data




