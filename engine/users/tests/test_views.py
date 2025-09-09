from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import UserView


User = get_user_model()


class UserViewViewSetTests(APITestCase):
    def setUp(self):
        self.u1 = User.objects.create_user(username="alice", password="pw")
        self.u2 = User.objects.create_user(username="bob", password="pw")
        self.base = reverse("user-views-list")  # /api/v1/user/views/

    def test_post_requires_authentication(self):
        resp = self.client.post(self.base, {"name": "View A", "metric_keys": [], "filters": {}}, format="json")
        # DRF may return 403 (CSRF) or 401 (no auth) depending on auth classes
        self.assertIn(resp.status_code, {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN})

    def test_create_and_retrieve_own_view(self):
        self.client.login(username="alice", password="pw")
        payload = {"name": "My Corners", "metric_keys": ["corners"], "filters": {"status": "LIVE"}}
        create = self.client.post(self.base, payload, format="json")
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        view_id = create.data["id"]

        obj = UserView.objects.get(pk=view_id)
        self.assertEqual(obj.user, self.u1)
        self.assertEqual(obj.name, "My Corners")

        detail_url = reverse("user-views-detail", kwargs={"pk": view_id})
        show = self.client.get(detail_url)
        self.assertEqual(show.status_code, status.HTTP_200_OK)
        self.assertEqual(show.data["name"], "My Corners")
        self.assertEqual(show.data["metric_keys"], ["corners"])

    def test_cannot_retrieve_someone_elses_view(self):
        v = UserView.objects.create(user=self.u1, name="Private View", metric_keys=["xg"], filters={})
        self.client.login(username="bob", password="pw")
        detail_url = reverse("user-views-detail", kwargs={"pk": str(v.id)})
        resp = self.client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)