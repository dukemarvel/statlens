from rest_framework import serializers
from .models import Competition, Season

class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ["id", "name", "country"]

class SeasonSerializer(serializers.ModelSerializer):
    competition = CompetitionSerializer(read_only=True)
    class Meta:
        model = Season
        fields = ["id", "competition", "name", "year_start", "year_end"]
