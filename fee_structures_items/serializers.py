from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from schoolgroups.serializers import SchoolGroupSerializer
from term.serializers import TermSerializer
from voteheads.serializers import VoteHeadSerializer
from .models import FeeStructureItem




class FeeStructureItemSerializer(serializers.ModelSerializer):
    votehead = VoteHeadSerializer()
    school_group = SchoolGroupSerializer()
    class Meta:
        model = FeeStructureItem
        fields = '__all__'


class FeeStructureItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructureItem
        fields = '__all__'