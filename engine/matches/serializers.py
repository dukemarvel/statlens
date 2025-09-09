from rest_framework import serializers
from .models import Match
from metrics.models import MatchMetric, MetricType
from metrics.serializers import MatchMetricSerializer

class MatchSerializer(serializers.ModelSerializer):
    home = serializers.UUIDField(source="home_id", read_only=True)
    away = serializers.UUIDField(source="away_id", read_only=True)
    selected_metrics = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            "id", "competition", "season", "utc_kickoff",
            "home", "away", "venue", "status", "minute",
            "freshness_ts", "selected_metrics",
        ]

    def get_selected_metrics(self, obj):
        """
        If the request has ?metrics=corners,cards_total[&period=FT],
        embed only those metrics for this match. Otherwise return [].
        """
        request = self.context.get("request")
        if not request:
            return []

        metrics_param = request.query_params.get("metrics")
        if not metrics_param:
            return []

        keys = [k.strip() for k in metrics_param.split(",") if k.strip()]
        period = request.query_params.get("period", "FT")

        if not keys:
            return []

        # Map keys → MetricType ids (bulk)
        type_map = dict(MetricType.objects.filter(key__in=keys).values_list("key", "id"))
        if not type_map:
            return []

        # Fetch metrics for this match in one query
        rows = (MatchMetric.objects
                .select_related("metric_type")
                .filter(match=obj, period=period, metric_type_id__in=type_map.values())
                .order_by("team_id"))
        return MatchMetricSerializer(rows, many=True).data