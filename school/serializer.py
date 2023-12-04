from rest_framework import serializers

from school.models import School
from school_categories.serializers import SchoolCategorySerializer
from school_types.serializers import SchoolTypeSerializer


class SchoolSerializer(serializers.ModelSerializer):
    school_type_details = SchoolTypeSerializer(source='school_type', required=False, read_only=True)
    school_category_details = SchoolCategorySerializer(source='school_category', required=False, read_only=True)

    class Meta:
        model = School
        fields = '__all__'
