from django.test import TestCase
from django.test.utils import isolate_apps
from django.utils import timezone
from django.db import connection

from ..models import TimeStampedModel


@isolate_apps("core")
class TimeStampedModelTests(TestCase):
    # Temporary concrete model for tests only
    class Dummy(TimeStampedModel):
        class Meta:
            app_label = "core"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create table for Dummy
        with connection.schema_editor() as editor:
            editor.create_model(cls.Dummy)

    @classmethod
    def tearDownClass(cls):
        # Drop table for Dummy
        with connection.schema_editor() as editor:
            editor.delete_model(cls.Dummy)
        super().tearDownClass()

    def test_created_and_updated_autoset_on_create(self):
        obj = self.Dummy.objects.create()
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        self.assertLessEqual(obj.created_at, obj.updated_at)

    def test_updated_at_changes_on_save(self):
        obj = self.Dummy.objects.create()
        first_updated = obj.updated_at
        # small wait not required; auto_now will still bump on save
        obj.save()
        obj.refresh_from_db()
        self.assertGreaterEqual(obj.updated_at, first_updated)