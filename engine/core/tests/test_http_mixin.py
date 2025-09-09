import hashlib
from django.test import TestCase, RequestFactory
from django.test.utils import isolate_apps
from django.http import HttpResponse
from django.utils import timezone
from django.db import connection

from ..http import ConditionalHeadersMixin
from ..models import TimeStampedModel


@isolate_apps("core")
class ConditionalHeadersMixinTests(TestCase):
    class Dummy(ConditionalHeadersMixin):
        pass

    # Temp model with updated_at so we can build a queryset
    class Stamp(TimeStampedModel):
        class Meta:
            app_label = "core"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create table for Stamp
        with connection.schema_editor() as editor:
            editor.create_model(cls.Stamp)

    @classmethod
    def tearDownClass(cls):
        # Drop table for Stamp
        with connection.schema_editor() as editor:
            editor.delete_model(cls.Stamp)
        super().tearDownClass()

    def setUp(self):
        self.factory = RequestFactory()
        self.mixin = self.Dummy()

    def test_sets_last_modified_and_etag_when_rows_exist(self):
        # Create two rows
        a = self.Stamp.objects.create()
        b = self.Stamp.objects.create()

        # Make b the latest by bumping updated_at
        newer = timezone.now() + timezone.timedelta(seconds=5)
        self.Stamp.objects.filter(id=b.id).update(updated_at=newer)

        request = self.factory.get("/api/v1/matches?foo=bar")
        response = HttpResponse()

        qs = self.Stamp.objects.all()
        response = self.mixin.set_conditional_headers(request, response, qs)

        self.assertIn("Last-Modified", response.headers)

        latest_ts = qs.order_by("-updated_at").values_list("updated_at", flat=True).first().timestamp()
        seed = f"{request.get_full_path()}::{latest_ts}"
        expected_etag = hashlib.md5(seed.encode()).hexdigest()
        self.assertEqual(response.headers.get("ETag"), expected_etag)

    def test_sets_only_etag_when_no_rows(self):
        # Ensure empty table
        self.Stamp.objects.all().delete()

        request = self.factory.get("/api/v1/competitions?page=2")
        response = HttpResponse()

        qs = self.Stamp.objects.none()
        response = self.mixin.set_conditional_headers(request, response, qs)

        self.assertNotIn("Last-Modified", response.headers)

        seed = f"{request.get_full_path()}::no-updates"
        expected_etag = hashlib.md5(seed.encode()).hexdigest()
        self.assertEqual(response.headers.get("ETag"), expected_etag)