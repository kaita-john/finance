from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from term.serializers import TermSerializer
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    term_details = TermSerializer(source='term',read_only=True, many=False)
    classes_details = ClassesSerializer(source='classes',read_only=True, many=False)
    academic_year_details = AcademicYearSerializer(source='academic_year',read_only=True, many=False)
    fee_structure_items = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'
        depth = 1


