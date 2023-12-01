from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from term.serializers import TermSerializer
from .models import FeeStructure

class FeeStructureSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    classes = ClassesSerializer()
    academic_year = AcademicYearSerializer()
    class Meta:
        model = FeeStructure
        fields = '__all__'


class FeeStructureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = '__all__'