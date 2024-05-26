from rest_framework import serializers

from fee_structures.models import FeeStructure
from schoolgroups.serializers import SchoolGroupSerializer
from voteheads.serializers import VoteHeadSerializer
from vouchers.models import Voucher
from .models import VoucherItem


class BasicVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id']


class VoucherItemSerializer(serializers.ModelSerializer):
    votehead_details = VoteHeadSerializer(source='votehead', many=False, read_only=True)
    voucher_details = BasicVoucherSerializer(source='voucher', many=False, read_only=True)

    class Meta:
        model = VoucherItem
        fields = '__all__'