from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from .models import Match
from .serializers import MatchSerializer
from metrics.models import MatchMetric
from rest_framework.response import Response
from metrics.serializers import MatchMetricSerializer
from core.http import ConditionalHeadersMixin


class MatchViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet, ConditionalHeadersMixin):
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
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        qs = self.get_queryset()
        return self.set_conditional_headers(request, response, qs)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        # for retrieve, use a QS limited to that object to compute headers
        obj_qs = self.get_queryset().filter(pk=kwargs["pk"])
        return self.set_conditional_headers(request, response, obj_qs)
    
    @action(detail=True, methods=["get"], url_path="metrics")
    def metrics(self, request, pk=None):
        """GET /api/v1/matches/{id}/metrics?period=FT"""
        period = request.query_params.get("period", "FT")
        qs = (MatchMetric.objects
              .select_related("metric_type")
              .filter(match_id=pk, period=period)
              .order_by("team_id", "metric_type__key"))
        return Response(MatchMetricSerializer(qs, many=True).data)
