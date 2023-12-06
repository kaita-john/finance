# serializers.py
from rest_framework import serializers
from .models import SchoolImage


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolImage
        fields = '__all__'



