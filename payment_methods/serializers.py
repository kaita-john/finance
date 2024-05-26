from rest_framework import serializers

from school.serializer import SchoolSerializer
from .models import *


class PaymentMethodSerializer(serializers.ModelSerializer):
    school_details  = SchoolSerializer(source='school', required=False, read_only=True)

    class Meta:
        model = PaymentMethod
        fields = '__all__'
