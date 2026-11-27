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
        patcher = patch.dict(activities, {"Test Activity": activity}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_removes_only_the_selected_participant(self):
        # Arrange
        email = "first@example.com"

        # Act
        response = self.client.delete(
            "/activities/Test Activity/signup", params={"email": email}
        )
        listing = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(
            listing.json()["Test Activity"]["participants"],
            ["other@example.com"],
        )

    def test_missing_activity_is_rejected(self):
        # Arrange
        email = "other@example.com"

        # Act
        response = self.client.delete(
            "/activities/Unknown Activity/signup", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(
            activities["Test Activity"]["participants"],
            ["first@example.com", "other@example.com"],
        )

    def test_missing_participant_is_rejected(self):
        # Arrange
        email = "missing@example.com"

        # Act
        response = self.client.delete(
            "/activities/Test Activity/signup", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Student not signed up for this activity")
        self.assertEqual(
            activities["Test Activity"]["participants"],
            ["first@example.com", "other@example.com"],
        )

    def test_unregister_without_email_is_rejected(self):
        # Arrange
        url = "/activities/Test Activity/signup"

        # Act
        response = self.client.delete(url)

        # Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            activities["Test Activity"]["participants"],
            ["first@example.com", "other@example.com"],
        )

    def test_removed_participant_can_sign_up_again(self):
        # Arrange
        email = "first@example.com"
        removed = self.client.delete(
            "/activities/Test Activity/signup", params={"email": email}
        )
        self.assertEqual(removed.status_code, 200)

        # Act
        response = self.client.post(
            "/activities/Test Activity/signup", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            activities["Test Activity"]["participants"],
            ["other@example.com", email],
        )
