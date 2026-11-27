import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app


class ApiTests(unittest.TestCase):
    def setUp(self):
        activity = {
            "description": "Test activity",
            "schedule": "Friday",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        }
        patcher = patch.dict(activities, {"Test Activity": activity}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_root_redirects_to_activity_page(self):
        # Arrange
        url = "/"

        # Act
        response = self.client.get(url, follow_redirects=False)

        # Assert
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/static/index.html")

    def test_static_activity_page_is_served(self):
        # Arrange
        url = "/static/index.html"

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mergington High School", response.text)

    def test_get_activities_returns_activity_details(self):
        # Arrange
        expected = {
            "Test Activity": {
                "description": "Test activity",
                "schedule": "Friday",
                "max_participants": 3,
                "participants": ["existing@example.com"],
            }
        }

        # Act
        response = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)

    def test_signup_is_visible_in_activity_listing(self):
        # Arrange
        email = "new@example.com"

        # Act
        response = self.client.post(
            "/activities/Test Activity/signup", params={"email": email}
        )
        listing = self.client.get("/activities")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(
            listing.json()["Test Activity"]["participants"],
            ["existing@example.com", email],
        )

    def test_duplicate_signup_is_rejected(self):
        # Arrange
        email = "existing@example.com"

        # Act
        response = self.client.post(
            "/activities/Test Activity/signup", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Student already signed up for this activity")
        self.assertEqual(activities["Test Activity"]["participants"], [email])

    def test_signup_for_unknown_activity_is_rejected(self):
        # Arrange
        email = "new@example.com"

        # Act
        response = self.client.post(
            "/activities/Unknown Activity/signup", params={"email": email}
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Activity not found")
        self.assertEqual(activities["Test Activity"]["participants"], ["existing@example.com"])

    def test_signup_without_email_is_rejected(self):
        # Arrange
        url = "/activities/Test Activity/signup"

        # Act
        response = self.client.post(url)

        # Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(activities["Test Activity"]["participants"], ["existing@example.com"])
