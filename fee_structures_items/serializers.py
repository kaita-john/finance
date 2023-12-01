from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from fee_structures.serializers import FeeStructureSerializer
from schoolgroups.serializers import SchoolGroupSerializer
from term.serializers import TermSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import FeeStructureItem




class FeeStructureItemSerializer(serializers.ModelSerializer):
    votehead = VoteHeadSerializer()
    school_group = SchoolGroupSerializer()
    fee_structure_id = FeeStructureSerializer()

    class Meta:
        model = FeeStructureItem
        fields = '__all__'


class FeeStructureItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructureItem
        fields = '__all__'