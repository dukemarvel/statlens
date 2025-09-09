from django.core.management.base import BaseCommand
from django.db import connection
from uuid import UUID

class Command(BaseCommand):
    help = "Run EXPLAIN ANALYZE on hot queries"

    def handle(self, *args, **kwargs):
        # ---- Replace these with real values from your DB ----
        date_yyyy_mm_dd = "2025-09-06"
        home_id = UUID("00000000-0000-0000-0000-000000000000")   # e.g. Portugal team UUID
        away_id = UUID("00000000-0000-0000-0000-000000000001")   # e.g. Spain team UUID
        match_id = UUID("00000000-0000-0000-0000-000000000002")  # a specific match UUID
        # ------------------------------------------------------

        queries = [
            # A) Live/FT board for a date + selected metric keys
            (
                """
                SELECT mm.match_id, mm.team_id, mt.key, mm.value
                FROM matches_match m
                JOIN metrics_matchmetric mm
                  ON mm.match_id = m.id AND mm.period = 'FT'
                JOIN metrics_metrictype mt
                  ON mt.id = mm.metric_type_id
                WHERE m.utc_kickoff::date = %s
                  AND m.status IN ('LIVE','FT')
                  AND mt.key IN ('corners','cards_total');
                """,
                (date_yyyy_mm_dd,)
            ),

            # B) H2H last 20 meetings (corners @ FT) between two teams
            (
                """
                SELECT mm.match_id, mm.team_id, mm.value
                FROM metrics_matchmetric mm
                JOIN metrics_metrictype mt
                  ON mt.id = mm.metric_type_id AND mt.key = 'corners'
                WHERE mm.period = 'FT'
                  AND mm.match_id IN (
                      SELECT id
                      FROM matches_match
                      WHERE (home_id = %s AND away_id = %s)
                         OR (home_id = %s AND away_id = %s)
                      ORDER BY utc_kickoff DESC
                      LIMIT 20
                  );
                """,
                (home_id, away_id, away_id, home_id)
            ),

            # C) All FT metrics for a specific match
            (
                """
                SELECT mt.key, mm.team_id, mm.value
                FROM metrics_matchmetric mm
                JOIN metrics_metrictype mt
                  ON mt.id = mm.metric_type_id
                WHERE mm.match_id = %s
                  AND mm.period = 'FT';
                """,
                (match_id,)
            ),
        ]

        with connection.cursor() as cur:
            for i, (sql, params) in enumerate(queries, start=1):
                self.stdout.write(self.style.MIGRATE_HEADING(f"[Query {i}]"))
                cur.execute("EXPLAIN ANALYZE " + sql, params)
                for row in cur.fetchall():
                    print(row[0])
                print()
