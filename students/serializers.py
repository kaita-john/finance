from rest_framework import serializers

from academic_year.serializers import AcademicYearSerializer
from classes.serializers import ClassesSerializer
from streams.serializers import StreamsSerializer
from students.models import Student


class StudentSerializer(serializers.ModelSerializer):
    current_Stream_details = StreamsSerializer(source='current_Stream', required=False, read_only=True)
    current_Class_details  = ClassesSerializer(source='current_Class', required=False, read_only=True)
    current_Year_details  = AcademicYearSerializer(source='current_Year', required=False, read_only=True)
    class Meta:
        model = Student
        fields = '__all__'
