from rest_framework import viewsets, mixins
from .models import Match
from .serializers import MatchSerializer
from metrics.models import MatchMetric
from rest_framework.response import Response


class MatchViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MatchSerializer

    def get_queryset(self):
        qs = (Match.objects
              .select_related("competition", "season")
              .order_by("utc_kickoff"))

        # Filters: ?date=YYYY-MM-DD
        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(utc_kickoff__date=date)

        # ?competition=<uuid>
        comp = self.request.query_params.get("competition")
        if comp:
            qs = qs.filter(competition_id=comp)

        # ?status=LIVE|FT|SCHED (comma-separated allowed)
        status = self.request.query_params.get("status")
        if status:
            statuses = [s.strip() for s in status.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        return qs

class MatchMetricsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /matches/{id}/metrics?period=FT  → all metrics for a match+period
    """
    serializer_class = None  # we'll return a simple JSON dict

    def list(self, request, *args, **kwargs):
        from metrics.serializers import MatchMetricSerializer
        match_id = kwargs["match_pk"] if "match_pk" in kwargs else kwargs["pk"]
        period = request.query_params.get("period", "FT")
        qs = (MatchMetric.objects
              .select_related("metric_type")
              .filter(match_id=match_id, period=period)
              .order_by("team_id", "metric_type__key"))
        ser = MatchMetricSerializer(qs, many=True)
        return Response(ser.data)
