from rest_framework import serializers
from school_categories.models import SchoolCategory

class SchoolCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolCategory
        fields = '__all__'
