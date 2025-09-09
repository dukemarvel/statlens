from rest_framework import viewsets, mixins
from .models import Competition, Season
from .serializers import CompetitionSerializer, SeasonSerializer

class CompetitionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Competition.objects.all().order_by("country", "name")
    serializer_class = CompetitionSerializer

class SeasonViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = SeasonSerializer

    def get_queryset(self):
        qs = Season.objects.select_related("competition").order_by("-year_start")
        comp = self.request.query_params.get("competition")
        if comp:
            qs = qs.filter(competition_id=comp)
        return qs
