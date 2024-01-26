from rest_framework import serializers

from term.models import Term


class TermSerializer(serializers.ModelSerializer):
    academic_year_id = serializers.SerializerMethodField()

    def get_academic_year_id(self, obj):
        return str(obj.academic_year.id) if obj.academic_year else None

    class Meta:
            model = Term
            fields = '__all__'
