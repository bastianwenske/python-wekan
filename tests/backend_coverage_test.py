"""Focused tests for backend coverage improvement based on actual methods."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from wekan.board import Board
from wekan.card import WekanCard
from wekan.user import WekanUser
from wekan.wekan_client import WekanAPIError, WekanClient
from wekan.wekan_list import WekanList

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestWekanClientBasics(unittest.TestCase):
    """Test basic WekanClient functionality that exists."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the authentication to avoid actual API calls
        with unittest.mock.patch.object(WekanClient, "_WekanClient__get_api_token") as mock_token:
            mock_token.return_value = ("user123", "token123", datetime.now())
            self.client = WekanClient("https://test.wekan.com", "user", "pass")

    def test_client_initialization(self):
        """Test client initialization sets basic properties."""
        self.assertEqual(self.client.base_url, "https://test.wekan.com")
        self.assertEqual(self.client.username, "user")
        self.assertEqual(self.client.password, "pass")
        self.assertEqual(self.client.user_id, "user123")
        self.assertEqual(self.client.token, "token123")

    def test_parse_iso_date(self):
        """Test ISO date parsing."""
        iso_string = "2023-01-15T10:30:45.123Z"
        parsed_date = self.client.parse_iso_date(iso_string)
        self.assertIsInstance(parsed_date, datetime)
        self.assertEqual(parsed_date.year, 2023)


class TestCardBasics(unittest.TestCase):
    """Test basic WekanCard functionality that exists."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the entire hierarchy
        self.mock_client = MagicMock(spec=WekanClient)
        self.mock_board = MagicMock(spec=Board)
        self.mock_list = MagicMock(spec=WekanList)

        # Set up relationships
        self.mock_client.user_id = "test_user"
        self.mock_board.client = self.mock_client
        self.mock_board.id = "board1"
        self.mock_list.board = self.mock_board
        self.mock_list.id = "list1"

        # Mock card data with required fields only
        self.mock_card_data = {
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

        self.mock_client.fetch_json.return_value = self.mock_card_data
        self.mock_client.parse_iso_date.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        # Create card
        self.card = WekanCard(parent_list=self.mock_list, card_id="card1")
        self.mock_client.fetch_json.reset_mock()

    def test_card_initialization(self):
        """Test card initialization with basic properties."""
        self.assertEqual(self.card.id, "card1")
        self.assertEqual(self.card.title, "Test Card")
        self.assertEqual(self.card.description, "Test description")

    def test_card_update(self):
        """Test updating card title and description."""
        self.card.update(title="New Title", description="New Description")

        expected_payload = {"title": "New Title", "description": "New Description"}
        # The method calls fetch_json twice - once for update, once for refresh
        self.assertEqual(self.mock_client.fetch_json.call_count, 2)
        call_args = self.mock_client.fetch_json.call_args_list[0]  # First call is the update
        self.assertEqual(call_args.kwargs["payload"], expected_payload)

    def test_card_delete(self):
        """Test deleting a card."""
        self.card.delete()
        self.mock_client.fetch_json.assert_called_once()

    def test_add_comment_actual_api(self):
        """Test adding comment with the actual API signature."""
        comment_text = "Test comment"
        mock_response = {"_id": "comment1"}
        self.mock_client.fetch_json.return_value = mock_response

        self.card.add_comment(comment_text)

        # Check the actual API call signature
        call_args = self.mock_client.fetch_json.call_args
        self.assertEqual(call_args.kwargs["http_method"], "POST")
        # The actual implementation uses "comment" key, not "text"
        expected_payload = {"authorId": "test_user", "comment": comment_text}
        self.assertEqual(call_args.kwargs["payload"], expected_payload)

    def test_assign_member(self):
        """Test assigning member to card."""
        self.card.assign_member("user123")
        # The method calls fetch_json twice - once for update, once for refresh
        self.assertEqual(self.mock_client.fetch_json.call_count, 2)

    def test_card_repr(self):
        """Test card string representation."""
        repr_str = repr(self.card)
        self.assertIn("card1", repr_str)
        self.assertIn("Test Card", repr_str)


class TestBoardBasics(unittest.TestCase):
    """Test basic Board functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=WekanClient)

        # Mock board data with all required fields
        self.mock_board_data = {
            "_id": "board1",
            "title": "Test Board",
            "slug": "test-board",
            "archived": False,
            "stars": 0,
            "members": [],
            "createdAt": "2023-01-01T12:00:00.000Z",
            "modifiedAt": "2023-01-01T12:00:00.000Z",
            "permission": "private",
            "color": "blue",
            "subtasksDefaultBoardId": None,
            "subtasksDefaultListId": None,
            "allowsSubtasks": True,
            "allowsAttachments": True,
            "allowsChecklists": True,
            "allowsComments": True,
            "allowsDescriptionTitle": True,
            "allowsDescriptionText": True,
            "allowsCardNumber": True,
            "allowsActivities": True,
            "allowsLabels": True,
            "allowsAssignee": True,
            "allowsMembers": True,
            "allowsRequestedBy": True,
            "allowsAssignedBy": True,
            "allowsReceivedDate": True,
            "allowsStartDate": True,
            "allowsEndDate": True,
            "allowsDueDate": True,
            "type": "board",
            "sort": 0,
            "description": "Test board description",
        }

        self.mock_client.fetch_json.return_value = self.mock_board_data
        self.mock_client.parse_iso_date.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        self.board = Board(client=self.mock_client, board_id="board1")
        self.mock_client.fetch_json.reset_mock()

    def test_board_initialization(self):
        """Test board initialization."""
        self.assertEqual(self.board.id, "board1")
        self.assertEqual(self.board.title, "Test Board")
        self.assertEqual(self.board.color, "blue")


class TestUserBasics(unittest.TestCase):
    """Test basic User functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_client = MagicMock(spec=WekanClient)

        # Mock user data with all required fields
        self.mock_user_data = {
            "_id": "user123",
            "username": "testuser",
            "emails": [{"address": "test@example.com", "verified": True}],
            "profile": {"fullname": "Test User"},
            "isAdmin": False,
            "loginDisabled": False,
            "authenticationMethod": "password",
            "createdAt": "2023-01-01T10:00:00.000Z",
            "modifiedAt": "2023-01-01T10:00:00.000Z",
            "sessionData": {},
            "services": {},
            "heartbeat": "2023-01-01T10:00:00.000Z",
        }

        self.mock_client.fetch_json.return_value = self.mock_user_data
        self.mock_client.parse_iso_date.side_effect = lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )

        self.user = WekanUser(client=self.mock_client, user_id="user123")
        self.mock_client.fetch_json.reset_mock()

    def test_user_initialization(self):
        """Test user initialization."""
        self.assertEqual(self.user.id, "user123")
        self.assertEqual(self.user.username, "testuser")


class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling."""

    def test_wekan_api_error_creation(self):
        """Test creating WekanAPIError."""
        error = WekanAPIError("Test error", 500)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 500)

    def test_error_inheritance(self):
        """Test error class inheritance."""
        from wekan.wekan_client import WekanAuthenticationError, WekanNotFoundError

        not_found = WekanNotFoundError("Not found", 404)
        auth_error = WekanAuthenticationError("Auth failed", 401)

        self.assertIsInstance(not_found, WekanAPIError)
        self.assertIsInstance(auth_error, WekanAPIError)


if __name__ == "__main__":
    unittest.main()
