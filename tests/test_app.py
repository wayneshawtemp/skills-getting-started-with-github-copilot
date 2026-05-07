import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        # Arrange
        url = "/"

        # Act
        response = client.get(url, follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self):
        """Test retrieving all activities"""
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Soccer Team" in data

    def test_get_activities_structure(self):
        """Test that activities have correct structure"""
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_contain_initial_participants(self):
        """Test that activities contain initial participants"""
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        # Arrange
        url = "/activities/Chess Club/signup"
        params = {"email": "newstudent@mergington.edu"}

        # Act
        response = client.post(url, params=params)
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        # Arrange
        email = "participant@mergington.edu"
        signup_url = "/activities/Programming Class/signup"

        # Act
        client.post(signup_url, params={"email": email})
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email in activities["Programming Class"]["participants"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signup returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"
        url = "/activities/Chess Club/signup"

        # Act
        response = client.post(url, params={"email": email})
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"].lower()

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        # Arrange
        url = "/activities/Nonexistent Activity/signup"

        # Act
        response = client.post(url, params={"email": "test@mergington.edu"})
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_signup_missing_email_parameter(self):
        """Test signup without email parameter"""
        # Arrange
        url = "/activities/Chess Club/signup"

        # Act
        response = client.post(url)

        # Assert
        assert response.status_code == 422

    def test_signup_empty_email(self):
        """Test signup with empty email"""
        # Arrange
        url = "/activities/Chess Club/signup"

        # Act
        response = client.post(url, params={"email": ""})

        # Assert
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # Arrange
        email = "michael@mergington.edu"
        url = "/activities/Chess Club/signup"

        # Act
        response = client.delete(url, params={"email": email})
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        # Arrange
        email = "daniel@mergington.edu"
        url = "/activities/Chess Club/signup"

        # Act
        client.delete(url, params={"email": email})
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_not_signed_up(self):
        """Test unregister for student not signed up"""
        # Arrange
        url = "/activities/Chess Club/signup"

        # Act
        response = client.delete(url, params={"email": "notstudent@mergington.edu"})
        data = response.json()

        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"].lower()

    def test_unregister_invalid_activity(self):
        """Test unregister from non-existent activity"""
        # Arrange
        url = "/activities/Nonexistent Activity/signup"

        # Act
        response = client.delete(url, params={"email": "test@mergington.edu"})
        data = response.json()

        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()

    def test_unregister_missing_email_parameter(self):
        """Test unregister without email parameter"""
        # Arrange
        url = "/activities/Chess Club/signup"

        # Act
        response = client.delete(url)

        # Assert
        assert response.status_code == 422

    def test_unregister_twice(self):
        """Test that unregistering twice fails"""
        # Arrange
        email = "testtwice@mergington.edu"
        signup_url = "/activities/Art Club/signup"

        client.post(signup_url, params={"email": email})

        # Act
        response1 = client.delete(signup_url, params={"email": email})
        response2 = client.delete(signup_url, params={"email": email})

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400


class TestErrorHandling:
    """Tests for error handling and edge cases"""

    def test_activity_name_case_sensitivity(self):
        """Test that activity names are case-sensitive"""
        # Arrange
        url = "/activities/chess club/signup"

        # Act
        response = client.post(url, params={"email": "test@mergington.edu"})

        # Assert
        assert response.status_code == 404

    def test_special_characters_in_activity_name(self):
        """Test activity name with special characters"""
        # Arrange
        url = "/activities/Activity & Club!/signup"

        # Act
        response = client.post(url, params={"email": "test@mergington.edu"})

        # Assert
        assert response.status_code == 404

    def test_activities_endpoint_response_structure(self):
        """Test the complete response structure of activities endpoint"""
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)

        required_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Swimming Club",
            "Art Club",
            "Drama Club",
            "Science Olympiad",
            "Debate Team"
        ]

        for activity in required_activities:
            assert activity in data