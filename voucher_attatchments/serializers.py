from rest_framework import serializers

from voteheads.serializers import VoteHeadSerializer
from vouchers.models import Voucher
from .models import VoucherAttatchment


class BasicVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id']


class VoucherAttatchmentSerializer(serializers.ModelSerializer):
    voucher_details = BasicVoucherSerializer(source='voucher', many=False, read_only=True)

    class Meta:
        model = VoucherAttatchment
        fields = '__all__'