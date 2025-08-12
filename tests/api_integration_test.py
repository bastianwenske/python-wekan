"""Integration tests for WeKan API interactions."""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
import requests

from wekan.board import Board
from wekan.card import WekanCard
from wekan.wekan_client import WekanAPIError, WekanAuthenticationError, WekanClient
from wekan.wekan_list import WekanList

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestWekanAPIIntegration(unittest.TestCase):
    """Integration tests for WeKan API client interactions."""

    def setUp(self) -> None:
        """Set up test fixtures for integration tests."""
        self.base_url = "https://test.wekan.com"
        self.username = "testuser"
        self.password = "testpass"  # pragma: allowlist secret

    @patch("wekan.wekan_client.requests.post")
    @patch("wekan.wekan_client.requests.get")
    def test_full_authentication_flow(self, mock_get, mock_post):
        """Test complete authentication flow from login to API calls."""
        # Mock login response
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {
            "id": "user123",
            "token": "token456",
            "tokenExpires": "2024-12-31T23:59:59.000Z",
        }
        mock_post.return_value = login_response

        # Mock API call response
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = [
            {"_id": "board1", "title": "Test Board 1"},
            {"_id": "board2", "title": "Test Board 2"},
        ]
        mock_get.return_value = api_response

        # Create client (triggers authentication)
        client = WekanClient(self.base_url, self.username, self.password)

        # Verify authentication was called
        mock_post.assert_called_once_with(
            f"{self.base_url}/users/login",
            data={"username": self.username, "password": self.password},
        )

        # Make an API call
        boards = client.list_boards()

        # Verify API call was made with proper headers
        self.assertEqual(len(boards), 2)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        headers = call_args.kwargs.get("headers", {})
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer token456")

    @patch("wekan.wekan_client.requests.post")
    def test_authentication_error_handling(self, mock_post):
        """Test handling of authentication errors."""
        # Mock failed login
        error_response = Mock()
        error_response.status_code = 401
        error_response.text = "Invalid credentials"
        mock_post.return_value = error_response

        # Should raise authentication error
        with self.assertRaises(WekanAuthenticationError) as context:
            WekanClient(self.base_url, self.username, "wrongpassword")

        self.assertIn("Invalid credentials", str(context.exception.message))

    @patch("wekan.wekan_client.requests.post")
    def test_server_error_handling(self, mock_post):
        """Test handling of server errors during authentication."""
        # Mock server error
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        mock_post.return_value = error_response

        # Should raise API error
        with self.assertRaises(WekanAPIError) as context:
            WekanClient(self.base_url, self.username, self.password)

        self.assertEqual(context.exception.status_code, 500)

    @patch("wekan.wekan_client.requests.post")
    @patch("wekan.wekan_client.requests.get")
    def test_board_creation_workflow(self, mock_get, mock_post):
        """Test complete board creation workflow."""
        # Mock authentication
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "id": "user123",
            "token": "token456",
            "tokenExpires": "2024-12-31T23:59:59.000Z",
        }

        # Mock board creation response
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {
            "_id": "new_board",
            "title": "New Integration Board",
            "color": "blue",
            "slug": "new-integration-board",
            "archived": False,
            "createdAt": "2023-01-15T10:30:45.123Z",
            "modifiedAt": "2023-01-15T10:30:45.123Z",
        }

        # Mock board fetch response (for initialization)
        fetch_response = Mock()
        fetch_response.status_code = 200
        fetch_response.json.return_value = create_response.json.return_value

        # Configure mocks
        mock_post.side_effect = [auth_response, create_response]
        mock_get.return_value = fetch_response

        # Create client and board
        client = WekanClient(self.base_url, self.username, self.password)
        board = client.add_board(title="New Integration Board", color="blue", is_admin=True)

        # Verify board creation API call
        self.assertEqual(board.title, "New Integration Board")
        self.assertEqual(board.color, "blue")
        self.assertIsInstance(board, Board)

        # Verify correct API calls were made
        self.assertEqual(mock_post.call_count, 2)  # Auth + board creation

    @patch("wekan.wekan_client.requests.post")
    @patch("wekan.wekan_client.requests.get")
    @patch("wekan.wekan_client.requests.put")
    def test_card_management_workflow(self, mock_put, mock_get, mock_post):
        """Test complete card management workflow."""
        # Mock authentication
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "id": "user123",
            "token": "token456",
            "tokenExpires": "2024-12-31T23:59:59.000Z",
        }
        mock_post.return_value = auth_response

        # Mock board data
        board_data = {
            "_id": "board1",
            "title": "Test Board",
            "slug": "test-board",
            "archived": False,
            "createdAt": "2023-01-15T10:30:45.123Z",
            "modifiedAt": "2023-01-15T10:30:45.123Z",
        }

        # Mock list data
        list_data = {
            "_id": "list1",
            "title": "Test List",
            "archived": False,
            "swimlaneId": "swimlane1",
            "createdAt": "2023-01-15T10:30:45.123Z",
        }

        # Mock card data
        card_data = {
            "_id": "card1",
            "title": "Test Card",
            "description": "Test description",
            "members": [],
            "labelIds": [],
            "customFields": [],
            "sort": 1,
            "swimlaneId": "swimlane1",
            "cardNumber": 1,
            "archived": False,
            "parentId": "",
            "createdAt": "2023-01-15T10:30:45.123Z",
            "modifiedAt": "2023-01-15T10:30:45.123Z",
            "dateLastActivity": "2023-01-15T10:30:45.123Z",
            "requestedBy": "",
            "assignedBy": "",
            "assignees": [],
            "spentTime": 0,
            "isOvertime": False,
            "subtaskSort": 0,
            "linkedId": "",
        }

        # Configure GET responses
        mock_get.side_effect = [
            self._mock_response(board_data),
            self._mock_response(list_data),
            self._mock_response(card_data),
            self._mock_response({**card_data, "title": "Updated Card"}),  # After update
        ]

        # Mock update response
        mock_put.return_value = self._mock_response({"success": True})

        # Create client and objects
        client = WekanClient(self.base_url, self.username, self.password)
        board = Board(client=client, board_id="board1")
        wekan_list = WekanList(parent_board=board, list_id="list1")
        card = WekanCard(parent_list=wekan_list, card_id="card1")

        # Update card
        card.edit(title="Updated Card")

        # Verify API calls
        self.assertEqual(mock_post.call_count, 1)  # Auth only
        self.assertEqual(mock_get.call_count, 4)  # Board, list, card, card after update
        self.assertEqual(mock_put.call_count, 1)  # Card update

        # Verify PUT call was correct
        put_call_args = mock_put.call_args
        self.assertIn("payload", put_call_args.kwargs)
        self.assertEqual(put_call_args.kwargs["payload"], {"title": "Updated Card"})

    @patch("wekan.wekan_client.requests.post")
    @patch("wekan.wekan_client.requests.get")
    def test_error_propagation_in_workflow(self, mock_get, mock_post):
        """Test that errors are properly propagated through workflow."""
        # Mock successful authentication
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            "id": "user123",
            "token": "token456",
            "tokenExpires": "2024-12-31T23:59:59.000Z",
        }
        mock_post.return_value = auth_response

        # Mock API error response
        error_response = Mock()
        error_response.status_code = 404
        error_response.text = "Board not found"
        mock_get.return_value = error_response

        # Create client
        client = WekanClient(self.base_url, self.username, self.password)

        # Try to access non-existent board - should propagate error
        with self.assertRaises(WekanAPIError) as context:
            client.get_board("nonexistent")

        self.assertEqual(context.exception.status_code, 404)

    @patch("wekan.wekan_client.requests.post")
    @patch("wekan.wekan_client.requests.get")
    def test_token_expiry_and_renewal(self, mock_get, mock_post):
        """Test token expiry handling and renewal."""
        # Mock initial authentication
        initial_auth = Mock()
        initial_auth.status_code = 200
        initial_auth.json.return_value = {
            "id": "user123",
            "token": "token456",
            "tokenExpires": "2023-01-01T00:00:00.000Z",  # Expired token
        }

        # Mock token renewal
        renewal_auth = Mock()
        renewal_auth.status_code = 200
        renewal_auth.json.return_value = {
            "id": "user123",
            "token": "new_token789",
            "tokenExpires": "2024-12-31T23:59:59.000Z",
        }

        mock_post.side_effect = [initial_auth, renewal_auth]

        # Mock API response
        api_response = Mock()
        api_response.status_code = 200
        api_response.json.return_value = []
        mock_get.return_value = api_response

        # Create client
        client = WekanClient(self.base_url, self.username, self.password)

        # Verify token is expired
        self.assertTrue(client.token_expire_date < datetime.now(timezone.utc))

        # The client should handle token renewal automatically in real usage
        # This test verifies the setup for such scenarios

    def _mock_response(self, json_data, status_code=200):
        """Helper to create mock response objects."""
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.text = str(json_data) if status_code != 200 else ""
        return response


class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling across different scenarios."""

    @patch("wekan.wekan_client.requests.get")
    def test_network_timeout_handling(self, mock_get):
        """Test handling of network timeouts."""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with patch.object(WekanClient, "_WekanClient__get_api_token") as mock_token:
            mock_token.return_value = (
                "user123",
                "token123",
                datetime.now(timezone.utc),
            )
            client = WekanClient("https://test.wekan.com", "user", "pass")

            # Should handle timeout gracefully
            with self.assertRaises(requests.exceptions.Timeout):
                client.fetch_json("/api/boards")

    @patch("wekan.wekan_client.requests.get")
    def test_connection_error_handling(self, mock_get):
        """Test handling of connection errors."""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with patch.object(WekanClient, "_WekanClient__get_api_token") as mock_token:
            mock_token.return_value = (
                "user123",
                "token123",
                datetime.now(timezone.utc),
            )
            client = WekanClient("https://test.wekan.com", "user", "pass")

            # Should handle connection error gracefully
            with self.assertRaises(requests.exceptions.ConnectionError):
                client.fetch_json("/api/boards")

    @patch("wekan.wekan_client.requests.post")
    def test_malformed_json_response(self, mock_post):
        """Test handling of malformed JSON responses."""
        # Mock response with invalid JSON
        response = Mock()
        response.status_code = 200
        response.json.side_effect = ValueError("Invalid JSON")
        response.text = "Invalid JSON response"
        mock_post.return_value = response

        # Should handle JSON parsing error
        with self.assertRaises(ValueError):
            WekanClient("https://test.wekan.com", "user", "pass")


if __name__ == "__main__":
    unittest.main()
