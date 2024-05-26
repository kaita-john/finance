from rest_framework import serializers

from grants.models import Grant
from students.serializers import StudentSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import GrantItem


class BasicGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = ['school_id', 'id']


class GrantItemSerializer(serializers.ModelSerializer):
    votehead_details = VoteHeadSerializer(source='votehead', many=False, read_only=True)
    grant_details = BasicGrantSerializer(source='grant', many=False, read_only=True)

    class Meta:
        model = GrantItem
        fields = '__all__'