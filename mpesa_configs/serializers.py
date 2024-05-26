from rest_framework import serializers

from .models import Mpesaconfig


class MpesaconfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mpesaconfig
        fields = '__all__'
