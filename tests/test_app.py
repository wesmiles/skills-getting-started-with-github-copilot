"""
FastAPI endpoint tests using AAA (Arrange-Act-Assert) pattern.
Tests cover GET, POST, and DELETE endpoints for the activities API.
"""
import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index(self, client):
        """
        Test: Root endpoint redirects to static index.html
        
        Arrange: Initialize test client
        Act: GET /
        Assert: Status 307, Location header points to /static/index.html
        """
        # Arrange
        # client fixture is already set up
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, sample_activities):
        """
        Test: GET /activities returns all activities with correct structure
        
        Arrange: Client with sample_activities fixture
        Act: GET /activities
        Assert: Status 200, response contains all activities with required fields
        """
        # Arrange
        expected_activities_count = len(sample_activities)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activities_count
        
        # Verify each activity has required fields
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup_adds_participant(self, client):
        """
        Test: Successful signup adds email to participants list
        
        Arrange: Client, activity="Chess Club", email="new@school.edu"
        Act: POST /activities/Chess Club/signup?email=new@school.edu
        Assert: Status 200, participant added, list updated
        """
        # Arrange
        activity_name = "Chess Club"
        email = "new@school.edu"
        
        # Get initial participant count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in response_after.json()[activity_name]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Test: Signup with non-existent activity returns 404
        
        Arrange: Client, activity="Fake Club", email="test@school.edu"
        Act: POST /activities/Fake Club/signup?email=test@school.edu
        Assert: Status 404, detail="Activity not found"
        """
        # Arrange
        activity_name = "Fake Club"
        email = "test@school.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self, client):
        """
        Test: Duplicate signup (already registered) returns 400
        
        Arrange: Client, activity="Chess Club", email="michael@mergington.edu" (pre-existing)
        Act: POST /activities/Chess Club/signup?email=michael@mergington.edu
        Assert: Status 400, detail="Student already signed up for this activity"
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in sample_activities
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestRemove:
    """Tests for DELETE /activities/{activity_name}/remove endpoint."""

    def test_successful_removal_removes_participant(self, client):
        """
        Test: Successful removal removes email from participants list
        
        Arrange: Client, activity="Chess Club", email="michael@mergington.edu"
        Act: DELETE /activities/Chess Club/remove?email=michael@mergington.edu
        Assert: Status 200, participant removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Get initial participant count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity_name]["participants"])
        assert email in response_before.json()[activity_name]["participants"]
        
        # Act
        response = client.delete(f"/activities/{activity_name}/remove", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant was removed
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity_name]["participants"])
        assert final_count == initial_count - 1
        assert email not in response_after.json()[activity_name]["participants"]

    def test_remove_nonexistent_activity_returns_404(self, client):
        """
        Test: Remove from non-existent activity returns 404
        
        Arrange: Client, activity="Fake Club", email="test@school.edu"
        Act: DELETE /activities/Fake Club/remove?email=test@school.edu
        Assert: Status 404, detail="Activity not found"
        """
        # Arrange
        activity_name = "Fake Club"
        email = "test@school.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/remove", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_non_participant_returns_400(self, client):
        """
        Test: Remove non-member (not signed up) returns 400
        
        Arrange: Client, activity="Chess Club", email="notamember@school.edu"
        Act: DELETE /activities/Chess Club/remove?email=notamember@school.edu
        Assert: Status 400, detail="Student not signed up for this activity"
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notamember@school.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/remove", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"


class TestEdgeCases:
    """Tests for edge cases and combined operations."""

    def test_signup_then_remove_sequence(self, client):
        """
        Test: Signup then remove in sequence verifies state changes
        
        Arrange: Client, activity="Chess Club", email="test@school.edu", initial count
        Act: (1) POST signup, (2) DELETE remove
        Assert: Count +1 after signup, then -1 after remove (returns to initial)
        """
        # Arrange
        activity_name = "Chess Club"
        email = "test@school.edu"
        
        response_initial = client.get("/activities")
        initial_count = len(response_initial.json()[activity_name]["participants"])
        
        # Act: Signup
        response_signup = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert response_signup.status_code == 200
        
        response_after_signup = client.get("/activities")
        after_signup_count = len(response_after_signup.json()[activity_name]["participants"])
        assert after_signup_count == initial_count + 1
        
        # Act: Remove
        response_remove = client.delete(f"/activities/{activity_name}/remove", params={"email": email})
        assert response_remove.status_code == 200
        
        # Assert: Final count matches initial
        response_final = client.get("/activities")
        final_count = len(response_final.json()[activity_name]["participants"])
        assert final_count == initial_count

    def test_query_parameter_encoding_with_special_chars(self, client):
        """
        Test: Query parameter encoding handles special characters in email
        
        Arrange: Client, email with special chars (e.g., "test+tag@school.edu")
        Act: POST signup with encoded email parameter
        Assert: Status 200, email stored correctly
        """
        # Arrange
        activity_name = "Chess Club"
        email = "test+tag@school.edu"  # Email with special character
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        
        # Verify email was stored with special chars intact
        response_activities = client.get("/activities")
        participants = response_activities.json()[activity_name]["participants"]
        assert email in participants
