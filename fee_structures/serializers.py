from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from term.serializers import TermSerializer
from .models import FeeStructure


class FeeStructureSerializer(serializers.ModelSerializer):
    term_details = TermSerializer(source='term', required=False, read_only=True, many=False)
    classes_details = ClassesSerializer(source='classes', required=False, read_only=True, many=False)
    academic_year_details = AcademicYearSerializer(source='academic_year',required=False, read_only=True, many=False)
    fee_structure_values = serializers.ListField(child=serializers.DictField(), write_only=True)
    fee_structure_items = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FeeStructure
        fields = '__all__'

    def get_fee_structure_items(self, obj):
        from fee_structures_items.serializers import FeeStructureItemSerializer
        try:
            fee_structure_items = obj.fee_structure_items.all()
        except AttributeError:
            fee_structure_items = []
        return FeeStructureItemSerializer(fee_structure_items, many=True).data




