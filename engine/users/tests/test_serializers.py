from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from ..serializers import UserViewSerializer
from ..models import UserView


User = get_user_model()


class UserViewSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.u = User.objects.create_user(username="alice", password="pw")

    def test_create_sets_user_from_request_context(self):
        request = self.factory.post("/api/v1/user/views/")
        request.user = self.u

        serializer = UserViewSerializer(
            data={"name": "Corners Live", "metric_keys": ["corners"], "filters": {"status": "LIVE"}},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        self.assertIsInstance(instance, UserView)
        self.assertEqual(instance.user, self.u)
        self.assertEqual(instance.name, "Corners Live")
        self.assertEqual(instance.metric_keys, ["corners"])
        self.assertEqual(instance.filters, {"status": "LIVE"})

    def test_user_field_is_not_allowed_in_payload(self):
        """
        Serializer does not expose a 'user' writeable field;
        even if provided, it should be ignored and request.user used.
        """
        rogue = User.objects.create_user(username="mallory", password="pw")
        request = self.factory.post("/api/v1/user/views/")
        request.user = self.u

        payload = {
            "name": "My View",
            "metric_keys": ["cards_total"],
            "filters": {},
            # Pretend client tries to set a different user:
            "user": rogue.id,
        }
        serializer = UserViewSerializer(data=payload, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        self.assertEqual(instance.user, self.u)  # not rogue
        self.assertNotEqual(instance.user, rogue)
