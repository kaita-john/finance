from rest_framework import serializers

from streams.models import Stream


class StreamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'
