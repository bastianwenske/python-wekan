import random
from datetime import date, datetime

import pytest
import requests
from faker import Faker

from wekan import Board, Customfield, Integration, Swimlane, WekanClient
from wekan.card import WekanCard
from wekan.card_checklist import CardChecklist
from wekan.card_comment import CardComment
from wekan.user import WekanUser
from wekan.wekan_list import WekanList

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


fake = Faker()
wekan_id_length = 17
wekan_base_url = "http://localhost:8080"

# Global variables (initialized in respective test functions)
api: WekanClient = None  # type: ignore
new_user: WekanUser = None  # type: ignore
new_board: Board = None  # type: ignore
new_list: WekanList = None  # type: ignore
new_integration: Integration = None  # type: ignore
new_activity: list[str] = None  # type: ignore
new_swimlane: Swimlane = None  # type: ignore
new_custom_field: Customfield = None  # type: ignore
custom_field_types: list[str] = None  # type: ignore
new_card: WekanCard = None  # type: ignore
new_checklist: CardChecklist = None  # type: ignore
new_comment: dict = None  # type: ignore


def test_parse_iso_date() -> None:
    datetime_object = WekanClient.parse_iso_date("2022-05-22T22:08:14.869Z")
    assert isinstance(datetime_object, date)


def test_wekan_client() -> None:
    username = fake.name()
    password = fake.password(length=12)
    payload = {"username": username, "password": password, "email": fake.email()}
    res = requests.post(url=f"{wekan_base_url}/users/register", data=payload)
    assert res.status_code == 200

    global api  # this is global for being able to use the client in other tests
    api = WekanClient(base_url=wekan_base_url, username=username, password=password)
    assert len(api.token) == 43
    assert api.user_id is not None
    assert len(api.user_id) == wekan_id_length
    assert isinstance(api, WekanClient)


def test_get_users() -> None:
    all_users = api.get_users()
    user = all_users[0]
    assert isinstance(all_users, list)
    assert isinstance(user, WekanUser)
    assert isinstance(user.username, str)
    assert user.id is not None
    assert len(user.id) == wekan_id_length


def test_add_user() -> None:
    global new_user  # this is global for being able to use the user in other tests
    new_user = api.add_user(
        username=fake.email(), email=fake.email(), password=fake.password(length=12)
    )
    assert isinstance(new_user, WekanUser)
    assert isinstance(new_user.modified_at, date)
    assert new_user.id is not None
    assert len(new_user.id) == wekan_id_length


def test_add_board() -> None:
    colors = ["belize", "nephritis", "pomegranate", "pumpkin", "wisteria", "midnight"]
    global new_board  # this is global for being able to use the board in other tests
    new_board = api.add_board(title=f"{fake.first_name()}'s Board", color=random.choice(colors))
    assert isinstance(new_board, Board)
    assert isinstance(new_board.modified_at, date)
    assert isinstance(new_board.title, str)
    assert new_board.id is not None
    assert len(new_board.id) == wekan_id_length


def test_list_boards() -> None:
    all_boards = api.list_boards()
    board = all_boards[0]
    assert isinstance(all_boards, list)
    assert isinstance(board, Board)
    assert isinstance(board.title, str)
    assert board.id is not None
    assert len(board.id) == wekan_id_length


def test_create_list() -> None:
    global new_list  # this is global for being able to use the list in other tests
    new_list = new_board.create_list(title=fake.last_name())
    assert isinstance(new_list, WekanList)
    assert isinstance(new_list.sort, int)
    assert isinstance(new_list.created_at, date)
    assert new_list.id is not None
    assert len(new_list.id) == wekan_id_length


def test_get_lists() -> None:
    all_lists = new_board.get_lists()
    wekan_list = all_lists[0]
    assert isinstance(all_lists, list)
    assert isinstance(wekan_list, WekanList)
    assert isinstance(wekan_list.cards_count, int)
    assert wekan_list.id is not None
    assert len(wekan_list.id) == wekan_id_length


def test_add_integration() -> None:
    global new_integration  # this is global for being able to use the integration in other tests
    new_integration = new_board.add_integration(url=fake.url())
    assert isinstance(new_integration, Integration)
    assert isinstance(new_integration.modified_at, date)
    assert isinstance(new_integration.enabled, bool)
    assert new_integration.id is not None
    assert len(new_integration.id) == wekan_id_length


def test_list_integrations() -> None:
    all_integrations = new_board.list_integrations()
    single_integration = all_integrations[0]
    assert isinstance(all_integrations, list)
    assert isinstance(single_integration, Integration)
    assert isinstance(single_integration.modified_at, date)
    assert isinstance(single_integration.enabled, bool)
    assert single_integration.id is not None
    assert len(single_integration.id) == wekan_id_length


def test_edit_integration() -> None:
    title = fake.name()
    new_integration.edit(title=title)
    assert new_integration.id is not None
    updated_integration = new_board.get_integration_by_id(integration_id=new_integration.id)
    assert updated_integration.title == title


def test_change_title_integration() -> None:
    new_title = fake.name()
    print(new_title)
    new_integration.change_title(new_title=new_title)
    assert new_integration.id is not None
    updated_integration = new_board.get_integration_by_id(integration_id=new_integration.id)
    assert updated_integration.title == new_title


def test_add_activities_integration() -> None:
    global new_activity
    new_activity = [fake.word()]
    new_integration.add_activities(activities=new_activity)
    assert new_integration.id is not None
    updated_integration = new_board.get_integration_by_id(integration_id=new_integration.id)
    assert new_activity[0] in updated_integration.activities


def test_add_swimlane() -> None:
    swimlane_names = [
        "high prio",
        "expedite",
        "internal tasks",
        "tasks for customer",
        "low prio",
    ]
    global new_swimlane  # this is global for being able to use the swimlane in other tests
    new_swimlane = new_board.add_swimlane(title=random.choice(swimlane_names))
    assert isinstance(new_swimlane, Swimlane)
    assert isinstance(new_swimlane.updated_at, date)
    assert isinstance(new_swimlane.archived, bool)
    assert new_swimlane.id is not None
    assert len(new_swimlane.id) == wekan_id_length


def test_list_swimlanes() -> None:
    all_swimlanes = new_board.list_swimlanes()
    swimlane = all_swimlanes[0]
    assert isinstance(all_swimlanes, list)
    assert isinstance(swimlane, Swimlane)
    assert swimlane.id is not None
    assert len(swimlane.id) == wekan_id_length


def test_add_custom_field() -> None:
    global new_custom_field  # this is global for being able to use the CustomField in other tests
    global custom_field_types
    custom_field_types = [
        "text",
        "number",
        "date",
        "dropdown",
        "currency",
        "checkbox",
        "stringtemplate",
    ]
    # Workaround for settings parameter type mismatch
    settings_type = dict[str, str]
    new_custom_field = new_board.add_custom_field(
        name=fake.name(),
        show_label_on_minicard=False,
        automatically_on_card=False,
        show_on_card=True,
        field_type=random.choice(custom_field_types),
        settings=settings_type,
        show_sum_at_top_of_list=False,
    )
    assert isinstance(new_custom_field, Customfield)
    assert isinstance(new_custom_field.automatically_on_card, bool)
    assert isinstance(new_custom_field.show_on_card, bool)
    assert isinstance(new_custom_field.name, str)
    assert new_custom_field.id is not None
    assert len(new_custom_field.id) == wekan_id_length


def test_list_custom_fields() -> None:
    all_custom_fields = new_board.list_custom_fields()
    custom_field = all_custom_fields[0]
    assert isinstance(all_custom_fields, list)
    assert isinstance(custom_field, Customfield)
    assert custom_field.id is not None
    assert len(custom_field.id) == wekan_id_length


def test_edit_custom_field() -> None:
    new_name = fake.name()
    new_type = random.choice(custom_field_types)
    show_on_card = False
    data = {"name": new_name, "type": new_type, "showOnCard": show_on_card}
    new_custom_field.edit(data=data)
    assert new_custom_field.id is not None
    updated_field = new_board.get_custom_field_by_id(custom_field_id=new_custom_field.id)
    assert updated_field.name == new_name
    assert updated_field.type == new_type
    assert updated_field.show_on_card == show_on_card


def test_create_card() -> None:
    global new_card  # this is global for being able to use the card in other tests
    new_card = new_list.create_card(
        title=f"{fake.name()}'s Card",
        members=[new_user.id],
        description=fake.text(max_nb_chars=500),
    )
    assert isinstance(new_card, WekanCard)
    assert isinstance(new_card.archived, bool)
    assert isinstance(new_card.sort, int)
    assert isinstance(new_card.modified_at, date)
    assert new_card.id is not None
    assert len(new_card.id) == wekan_id_length


def test_edit_card() -> None:
    new_title = f"{fake.name()}'s Card"
    new_description = fake.text(max_nb_chars=500)
    due_at = datetime.now()
    requested_by = fake.name()
    new_card.edit(
        title=new_title,
        description=new_description,
        spent_time=12,
        due_at=due_at,
        requested_by=requested_by,
    )
    assert new_card.id is not None
    updated_card = new_list.get_card_by_id(card_id=new_card.id)
    assert updated_card.title == new_title
    assert updated_card.description == new_description
    assert updated_card.spent_time == 12
    assert updated_card.requested_by == requested_by
    assert isinstance(updated_card.due_at, date)


def test_add_card_checklist() -> None:
    global new_checklist  # this is global for being able to use the checklist in other tests
    new_checklist = new_card.add_checklist(title=f"{fake.name()}'s Checklist")
    assert isinstance(new_checklist, CardChecklist)
    assert isinstance(new_checklist.sort, int)
    assert isinstance(new_checklist.createdAt, date)


def test_list_card_checklists() -> None:
    all_checklists = new_card.get_checklists()
    checklist = all_checklists[0]
    assert isinstance(all_checklists, list)
    assert isinstance(checklist, CardChecklist)
    assert checklist.id is not None
    assert len(checklist.id) == wekan_id_length


# This is the test for testing the list of CardChecklistItems.
# Not working due we are not able to create CardCheckListItem via api.
# This is not supported currently by API.
# So this procedure will cause "IndexError: list index out of range"
#
# def test_list_card_checklist_items():
#     all_checklist_items = new_checklist.list_checklists()
#     checklist_item = all_checklist_items[0]
#     assert isinstance(all_checklist_items, list)
#     assert isinstance(checklist_item, CardChecklistItem)
#     assert isinstance(checklist_item.is_finished, bool)
#     assert isinstance(checklist_item.sort, int)
#     assert len(checklist_item.id) == wekan_id_length


def test_add_card_comment() -> None:
    global new_comment  # this is global for being able to use the comment in other tests
    text = fake.text(max_nb_chars=100)
    new_comment = new_card.add_comment(text=text)
    assert isinstance(new_comment, dict)
    assert new_comment["cardId"] == new_card.id


def test_get_card_comments() -> None:
    all_comments = new_card.get_comments()
    comment = all_comments[0]
    assert isinstance(all_comments, list)
    assert isinstance(comment, dict)
    assert len(comment["_id"]) == wekan_id_length


def test_eq() -> None:
    assert new_board == new_board
    assert new_swimlane == new_swimlane
    assert new_card == new_card
    assert new_list == new_list


def test_delete_card_comment() -> None:
    # Re-fetch the comment as a CardComment object to delete it
    comment_to_delete = CardComment(parent_card=new_card, comment_id=new_comment["_id"])
    try:
        comment_to_delete.delete()
        assert new_comment["_id"] not in [c["_id"] for c in new_card.get_comments()]
    except Exception as e:
        pytest.fail(f"Failed to delete comment: {str(e)}")


def test_delete_card_checklist() -> None:
    try:
        new_checklist.delete()
        assert new_checklist.id not in [checklist.id for checklist in new_card.get_checklists()]
    except Exception as e:
        pytest.fail(f"Failed to delete checklist: {str(e)}")


def test_delete_card() -> None:
    try:
        new_card.delete()
        assert new_card.id not in [card.id for card in new_list.get_cards()]
    except Exception as e:
        pytest.fail(f"Failed to delete card: {str(e)}")


def test_delete_swimlane() -> None:
    try:
        new_swimlane.delete()
        assert new_swimlane.id not in [swimlane.id for swimlane in new_board.list_swimlanes()]
    except Exception as e:
        pytest.fail(f"Failed to delete swimlane: {str(e)}")


def test_delete_list() -> None:
    try:
        new_list.delete()
        assert new_list.id not in [wlist.id for wlist in new_board.get_lists()]
    except Exception as e:
        pytest.fail(f"Failed to delete list: {str(e)}")


def test_delete_integration_activities() -> None:
    try:
        new_integration.delete_activities(activities=new_activity)
        assert new_integration.id is not None
        updated_integration = new_board.get_integration_by_id(new_integration.id)
        assert new_activity[0] not in updated_integration.activities
    except Exception as e:
        pytest.fail(f"Failed to delete integration activities: {str(e)}")


def test_delete_integration() -> None:
    try:
        new_integration.delete()
        assert new_integration.id not in [
            integration.id for integration in new_board.list_integrations()
        ]
    except Exception as e:
        pytest.fail(f"Failed to delete integration: {str(e)}")


def test_delete_custom_field() -> None:
    try:
        new_custom_field.delete()
        assert new_custom_field.id not in [
            custom_field.id for custom_field in new_board.list_custom_fields()
        ]
    except Exception as e:
        pytest.fail(f"Failed to delete custom field: {str(e)}")


def test_delete_board() -> None:
    try:
        new_board.delete()
        assert new_board.id not in [board.id for board in api.list_boards()]
    except Exception as e:
        pytest.fail(f"Failed to delete board: {str(e)}")


def test_delete_user() -> None:
    try:
        new_user.delete()
        assert new_user.id not in [user.id for user in api.get_users()]
    except Exception as e:
        pytest.fail(f"Failed to delete user: {str(e)}")
