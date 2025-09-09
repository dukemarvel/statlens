from rest_framework import serializers
from .models import MetricType, MatchMetric

class MetricTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricType
        fields = ["id", "key", "unit", "display_name", "decimals"]

class MatchMetricSerializer(serializers.ModelSerializer):
    metric_key = serializers.CharField(source="metric_type.key", read_only=True)
    class Meta:
        model = MatchMetric
        fields = ["metric_key", "team", "period", "value", "source", "confidence"]
