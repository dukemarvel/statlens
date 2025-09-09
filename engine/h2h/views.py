from rest_framework.views import APIView
from rest_framework.response import Response
from .models import H2HCache

class H2HView(APIView):
    """
    GET /h2h?home=&away=&metric=&window=5y
    Returns cached payload or 404 if not computed yet (MVP).
    """
    def get(self, request):
        home = request.query_params.get("home")
        away = request.query_params.get("away")
        metric = request.query_params.get("metric", "corners")
        window = request.query_params.get("window", "5y")

        if not (home and away):
            return Response({"detail": "home and away are required"}, status=400)

        try:
            cache = H2HCache.objects.get(home_id=home, away_id=away, metric_key=metric, window=window)
            return Response({
                "home": str(cache.home_id),
                "away": str(cache.away_id),
                "metric": cache.metric_key,
                "window": cache.window,
                "payload": cache.payload,
                "updated_at_source": cache.updated_at_source,
            })
        except H2HCache.DoesNotExist:
            return Response({"detail": "H2H not yet materialized"}, status=404)
