from rest_framework import serializers

from vouchers.models import Voucher
from .models import VoucherAttachment


class BasicVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id']


class Voucherattachmentserializer(serializers.ModelSerializer):
    voucher_details = BasicVoucherSerializer(source='voucher', many=False, read_only=True)

    class Meta:
        model = VoucherAttachment
        fields = '__all__'