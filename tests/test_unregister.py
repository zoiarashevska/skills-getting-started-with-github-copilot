import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class UnregisterTests(unittest.TestCase):
    def setUp(self):
        activity = {
            "description": "Test",
            "schedule": "Friday",
            "max_participants": 3,
            "participants": ["first@example.com", "other@example.com"],
        }
        patcher = patch.dict(activities, {"Test Activity": activity})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def test_removes_only_the_selected_participant(self):
        response = self.client.delete(
            "/activities/Test Activity/signup", params={"email": "first@example.com"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get("/activities").json()["Test Activity"]["participants"],
            ["other@example.com"],
        )

    def test_missing_activity_or_participant(self):
        missing_activity = self.client.delete(
            "/activities/Unknown Activity/signup", params={"email": "other@example.com"}
        )
        missing_participant = self.client.delete(
            "/activities/Test Activity/signup", params={"email": "missing@example.com"}
        )

        self.assertEqual(missing_activity.status_code, 404)
        self.assertEqual(missing_participant.status_code, 404)
        self.assertEqual(
            activities["Test Activity"]["participants"],
            ["first@example.com", "other@example.com"],
        )
