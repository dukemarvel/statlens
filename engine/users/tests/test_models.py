from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import UserProfile, UserView


User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="alice", password="pw")
        self.u2 = User.objects.create_user(username="bob", password="pw")

    def test_userprofile_str(self):
        p = UserProfile.objects.create(user=self.u1, default_metric_keys=["corners"], timezone="Africa/Lagos")
        self.assertEqual(str(p), f"Profile({self.u1})")
        self.assertEqual(p.default_metric_keys, ["corners"])
        self.assertEqual(p.timezone, "Africa/Lagos")

    def test_userview_str_and_unique_per_user_but_not_across_users(self):
        v1 = UserView.objects.create(user=self.u1, name="My EPL", metric_keys=["corners"], filters={"status": "LIVE"})
        self.assertEqual(str(v1), f"{self.u1}: My EPL")

        # Same name allowed for a different user (no IntegrityError)
        v2 = UserView.objects.create(user=self.u2, name="My EPL", metric_keys=["cards_total"], filters={})
        self.assertEqual(v2.name, "My EPL")
        self.assertEqual(v2.user, self.u2)
