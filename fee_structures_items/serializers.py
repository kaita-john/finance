from rest_framework import serializers

from fee_structures.models import FeeStructure
from schoolgroups.serializers import SchoolGroupSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import FeeStructureItem


class BasicFeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = ['id', 'term', 'classes', 'academic_year', 'instructions', 'school_id']


class FeeStructureItemSerializer(serializers.ModelSerializer):
    votehead_details = VoteHeadSerializer(source='votehead', many=False, read_only=True)
    school_group_details = SchoolGroupSerializer(source='school_group', many=False, read_only=True)
    fee_Structure_details = BasicFeeStructureSerializer(source='fee_Structure', read_only=True)

    class Meta:
        model = FeeStructureItem
        fields = '__all__'