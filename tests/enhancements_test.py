from collections.abc import Generator
from datetime import datetime

import pytest

# Assuming 'api' is a globally available WekanClient instance, initialized in test_cases.py
# This is not ideal, but follows the existing test structure.
from tests.cases_test import api, fake
from wekan.board import Board
from wekan.card import WekanCard
from wekan.wekan_list import WekanList

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")  # type: ignore[misc]
def test_board() -> Generator[Board, None, None]:
    assert api is not None, "API client not initialized"
    board = api.add_board(
        title=f"Test Board for Enhancements - {fake.first_name()}", color="midnight"
    )
    yield board
    # Teardown: delete the board after tests are done
    board.delete()


def test_board_update(test_board: Board) -> None:
    """Test updating a board's properties."""
    new_title = f"Updated Title - {fake.last_name()}"
    new_description = fake.sentence()
    test_board.update(title=new_title, description=new_description)

    # Re-fetch the board to verify the update
    # This assumes a method to get a board by ID, which is a good addition.
    # For now, we list all boards and find it.
    assert api is not None, "API client not initialized"
    updated_board = [b for b in api.list_boards() if b.id == test_board.id][0]

    assert updated_board.title == new_title
    # Note: The 'description' attribute is not explicitly on the Board object in the original code.
    # This test would fail unless we add it. Let's assume description is part of the raw data.
    # Note: accessing private attribute for testing purposes
    assert (
        hasattr(updated_board, "_Board__raw_data")
        and updated_board._Board__raw_data.get("description") == new_description
    )


def test_board_archive_and_restore(test_board: Board) -> None:
    """Test archiving and restoring a board."""
    test_board.archive()
    assert test_board.archived is True

    # Verify from the API
    assert api is not None, "API client not initialized"
    refetched_board = [b for b in api.list_boards() if b.id == test_board.id][0]
    assert refetched_board.archived is True

    test_board.restore()
    assert test_board.archived is False

    # Verify from the API again
    assert api is not None, "API client not initialized"
    refetched_board_restored = [b for b in api.list_boards() if b.id == test_board.id][0]
    assert refetched_board_restored.archived is False


def test_board_member_management(test_board: Board) -> None:
    """Test getting members and adding a new one."""
    # First, get a user to add
    assert api is not None, "API client not initialized"
    users = api.get_users()
    if not users:
        pytest.skip("No users found to test member management.")

    a_user = users[-1]  # Pick a user that is likely not the admin

    initial_members = test_board.get_members()

    # Add a member
    assert a_user.id is not None, "User ID is None"
    test_board.add_member(a_user.id, role="normal")

    # Verify
    updated_members = test_board.get_members()
    assert len(updated_members) == len(initial_members) + 1
    assert any(m["userId"] == a_user.id for m in updated_members)


def test_list_management(test_board: Board) -> None:
    """Test list creation, update, archive, and restore."""
    # Create
    new_list = test_board.create_list("My New List")
    assert isinstance(new_list, WekanList)
    assert new_list.title == "My New List"

    # Update
    updated_title = "Updated List Title"
    new_list.update(title=updated_title)
    assert new_list.title == updated_title

    # Archive and Restore
    new_list.archive()
    assert new_list.archived is True
    new_list.restore()
    assert new_list.archived is False


def test_card_management(test_board: Board) -> None:
    """Test card creation and the new wrapper methods."""
    a_list = test_board.create_list("Card Test List")

    # Create
    card = a_list.create_card("My Test Card", description="Initial description.")
    assert isinstance(card, WekanCard)
    assert card.title == "My Test Card"

    # Update
    card.update(title="Updated Card Title", description="Updated description.")
    assert card.title == "Updated Card Title"
    assert card.description == "Updated description."

    # Move
    another_list = test_board.create_list("Another List")
    card.move_to_list(another_list)
    # Note: assuming list_id attribute exists or using a different check
    assert hasattr(card, "list_id") and card.list_id == another_list.id

    # Dates
    due_date = datetime.utcnow()
    card.set_due_date(due_date)
    # The time precision might differ, so we check the date part
    assert (
        card.due_at is not None
        and hasattr(card.due_at, "date")
        and card.due_at.date() == due_date.date()
    )

    # Assign member
    assert api is not None, "API client not initialized"
    users = api.get_users()
    if not users:
        pytest.skip("No users to test assignment.")
    a_user = users[-1]

    assert a_user.id is not None, "User ID is None"
    card.assign_member(a_user.id)
    assert a_user.id in card.members
