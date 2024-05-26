from django.contrib.auth.models import Group
from rest_framework import serializers


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']
