from rest_framework import serializers
from school_types.models import SchoolType

class SchoolTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolType
        fields = '__all__'
