from rest_framework import serializers

from classes.models import Classes


class ClassesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classes
        fields = '__all__'
