from rest_framework import serializers

from school.models import School
from school_categories.serializers import SchoolCategorySerializer
from school_types.serializers import SchoolTypeSerializer



class SchoolSerializer(serializers.ModelSerializer):
    school_type = SchoolTypeSerializer(required=False)
    school_category = SchoolCategorySerializer(required=False)
    class Meta:
        model = School
        fields = '__all__'


class SchoolCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'


