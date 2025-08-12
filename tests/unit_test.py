import unittest
from unittest.mock import MagicMock

import pytest

from wekan.board import Board
from wekan.card import WekanCard
from wekan.wekan_client import WekanClient
from wekan.wekan_list import WekanList

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestBoardUnit(unittest.TestCase):

    def setUp(self) -> None:
        # Mock WekanClient
        self.mock_client = MagicMock(spec=WekanClient)
        self.mock_client.user_id = "test_user_id"

        # A mock raw data for a board
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
            "description": "Initial board description",
        }

        # Configure the mock fetch_json to return the board data when called for the board
        self.mock_client.fetch_json.return_value = self.mock_board_data

        # Instantiate the Board object with the mocked client
        self.board = Board(client=self.mock_client, board_id="board1")

        # Reset call counts before each test
        self.mock_client.fetch_json.reset_mock()

    def test_board_update(self) -> None:
        """Test the update method of the Board class."""
        new_title = "Updated Board Title"
        new_description = "Updated description."

        # Mock the return value for the __init__ call that happens after the update
        self.mock_client.fetch_json.return_value = {
            **self.mock_board_data,
            "title": new_title,
            "description": new_description,
        }

        self.board.update(title=new_title, description=new_description)

        # Check that fetch_json was called with the correct parameters for the update
        self.mock_client.fetch_json.assert_any_call(
            f"/api/boards/{self.board.id}",
            http_method="PUT",
            payload={"title": new_title, "description": new_description},
        )

        # Check that the board's attributes were updated
        self.assertEqual(self.board.title, new_title)

    def test_board_archive(self) -> None:
        """Test the archive method of the Board class."""
        self.board.archive()

        self.mock_client.fetch_json.assert_called_once_with(
            f"/api/boards/{self.board.id}/archive", http_method="POST"
        )
        self.assertTrue(self.board.archived)

    def test_board_restore(self) -> None:
        """Test the restore method of the Board class."""
        # First, archive it to have something to restore
        self.board.archived = True

        self.board.restore()

        self.mock_client.fetch_json.assert_called_once_with(
            f"/api/boards/{self.board.id}/restore", http_method="POST"
        )
        self.assertFalse(self.board.archived)

    def test_get_members(self) -> None:
        """Test getting board members."""
        mock_members = [{"userId": "user1"}, {"userId": "user2"}]
        self.mock_client.fetch_json.return_value = mock_members

        members = self.board.get_members()

        self.mock_client.fetch_json.assert_called_once_with(f"/api/boards/{self.board.id}/members")
        self.assertEqual(members, mock_members)


class TestListAndCardUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock(spec=WekanClient)
        self.mock_client.user_id = "test_user_id"
        self.mock_board = MagicMock(spec=Board)
        self.mock_board.client = self.mock_client
        self.mock_board.id = "board1"

        self.mock_list_data = {
            "_id": "list1",
            "title": "Test List",
            "archived": False,
            "swimlaneId": "swimlane1",
            "createdAt": "2023-01-01T12:00:00.000Z",
            "updatedAt": "2023-01-01T12:00:00.000Z",
            "sort": 0,
            "wipLimit": {},
            "color": "white",
        }
        self.mock_client.fetch_json.return_value = self.mock_list_data
        self.list = WekanList(parent_board=self.mock_board, list_id="list1")
        self.mock_client.fetch_json.reset_mock()

    def test_list_update(self) -> None:
        self.list.update(title="New List Title")
        self.mock_client.fetch_json.assert_any_call(
            "/api/boards/board1/lists/list1",
            http_method="PUT",
            payload={"title": "New List Title"},
        )

    def test_card_creation(self) -> None:
        self.mock_client.fetch_json.return_value = {
            "_id": "card1",
            "title": "New Card",
            "description": "desc",
            "members": [],
            "swimlaneId": "swimlane1",
            "listId": "list1",
            "boardId": "board1",
            "createdAt": "2023-01-01T12:00:00.000Z",
            "modifiedAt": "2023-01-01T12:00:00.000Z",
            "dateLastActivity": "2023-01-01T12:00:00.000Z",
            "archived": False,
            "sort": 0,
            "cardNumber": 1,
            "parentId": "",
            "labelIds": [],
            "customFields": [],
            "requestedBy": "",
            "assignedBy": "",
            "assignees": [],
            "spentTime": 0,
            "isOvertime": False,
            "subtaskSort": 0,
            "linkedId": "",
            "coverId": None,
            "vote": None,
            "poker": None,
            "targetId_gantt": None,
            "linkType_gantt": None,
            "linkId_gantt": None,
            "dueAt": None,
        }
        card = self.list.create_card(title="New Card", description="desc")
        self.assertIsInstance(card, WekanCard)
        self.assertEqual(card.title, "New Card")


if __name__ == "__main__":
    unittest.main()
