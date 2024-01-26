from rest_framework import serializers

from term.models import Term


class TermSerializer(serializers.ModelSerializer):
    academic_year_id = serializers.UUIDField(source='academic_year.id', read_only=True)

    class Meta:
        model = Term
        fields = '__all__'
