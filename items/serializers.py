from rest_framework import serializers

from students.serializers import StudentSerializer
from .models import Item


class BasicBursarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['school_id', 'student']


class ItemSerializer(serializers.ModelSerializer):
    student_details = StudentSerializer(source='student', many=False, read_only=True)
    bursary_details = BasicBursarySerializer(source='bursary', many=False, read_only=True)

    class Meta:
        model = Item
        fields = '__all__'