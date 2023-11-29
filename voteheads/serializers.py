from rest_framework import serializers

from account_types.models import AccountType
from account_types.serializers import AccountTypeSerializer
from voteheads.models import VoteHead


class VoteHeadSerializer(serializers.ModelSerializer):
    #account_type = serializers.PrimaryKeyRelatedField(queryset=AccountType.objects.all())
    account_type =AccountTypeSerializer()
    class Meta:
        model = VoteHead
        fields = '__all__'

class VoteHeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteHead
        fields = '__all__'
