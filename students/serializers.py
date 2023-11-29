from rest_framework import serializers

from streams.serializers import StreamsSerializer
from students.models import Student

class StudentSerializer(serializers.ModelSerializer):
    stream = StreamsSerializer()
    class Meta:
        model = Student
        fields = '__all__'

class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'