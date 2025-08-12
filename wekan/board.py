from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from wekan.wekan_client import WekanClient

import re

from wekan.base import WekanBase
from wekan.customfield import Customfield
from wekan.integration import Integration
from wekan.label import Label
from wekan.swimlane import Swimlane
from wekan.wekan_list import WekanList


class Board(WekanBase):
    def __init__(self, client: WekanClient, board_id: str) -> None:
        """Reference to a Wekan board."""
        super().__init__()
        self.client = client
        self.id = board_id

        self.__raw_data = self.client.fetch_json(f"/api/boards/{self.id}")
        self.title = self.__raw_data["title"]
        self.slug = self.__raw_data.get("slug", "")
        self.archived = self.__raw_data["archived"]
        self.stars = self.__raw_data["stars"]
        self.members = self.__raw_data["members"]
        self.created_at = self.client.parse_iso_date(self.__raw_data["createdAt"])
        self.modified_at = self.client.parse_iso_date(self.__raw_data["modifiedAt"])
        self.permission = self.__raw_data["permission"]
        self.color = self.__raw_data["color"]
        self.subtasks_default_board_id = self.__raw_data["subtasksDefaultBoardId"]
        self.subtasks_default_list_id = self.__raw_data["subtasksDefaultListId"]
        self.allows_card_counterList = self.__raw_data.get("allowsCardCounterList", None)
        self.allows_board_member_list = self.__raw_data.get("allowsBoardMemberList", None)
        self.date_settings_default_board_id = self.__raw_data.get(
            "dateSettingsDefaultBoardId", None
        )
        self.date_settings_default_list_id = self.__raw_data.get("dateSettingsDefaultListId", None)
        self.allow_subtasks = self.__raw_data["allowsSubtasks"]
        self.allows_attachments = self.__raw_data["allowsAttachments"]
        self.allows_checklists = self.__raw_data["allowsChecklists"]
        self.allows_comments = self.__raw_data["allowsComments"]
        self.allows_description_title = self.__raw_data["allowsDescriptionTitle"]
        self.allows_description_text = self.__raw_data["allowsDescriptionText"]
        self.allows_description_text_on_minicard = self.__raw_data.get(
            "allowsDescriptionTextOnMinicard", None
        )
        self.allows_card_number = self.__raw_data["allowsCardNumber"]
        self.allows_activities = self.__raw_data["allowsActivities"]
        self.allows_labels = self.__raw_data["allowsLabels"]
        self.allows_creator = self.__raw_data.get("allowsCreator", None)
        self.allows_assignee = self.__raw_data["allowsAssignee"]
        self.allows_members = self.__raw_data["allowsMembers"]
        self.allows_requested_by = self.__raw_data["allowsRequestedBy"]
        self.allows_card_sorting_by_number = self.__raw_data.get("allowsCardSortingByNumber", None)
        self.allows_show_lists = self.__raw_data.get("allowsShowLists", None)
        self.allows_assigned_by = self.__raw_data["allowsAssignedBy"]
        self.allows_received_date = self.__raw_data["allowsReceivedDate"]
        self.allows_start_date = self.__raw_data["allowsStartDate"]
        self.allows_end_date = self.__raw_data["allowsEndDate"]
        self.allows_due_date = self.__raw_data["allowsDueDate"]
        self.present_parent_task = self.__raw_data.get("presentParentTask", None)
        self.is_overtime = self.__raw_data.get("isOvertime", None)
        self.type = self.__raw_data["type"]
        self.sort = self.__raw_data["sort"]

    def __repr__(self) -> str:
        return f"<Board (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(
        cls,
        client: WekanClient,
        data: dict,
    ) -> Board:
        """
        Creates an instance of class Customfield by using the API-Response of Customfield creation.
        :param client: Instance of the wekan api client
        :param data: Response of CustomField creation
        :return: Instance of class CustomField
        """
        return cls(client=client, board_id=data["_id"])

    @classmethod
    def from_list(cls, client: WekanClient, data: dict) -> list[Board]:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param client: Instance of the wekan api client
        :param data: Responses of GET Boards
        :return Instances of class Board
        :rtype list
        """
        instances = []
        for board in data:
            instances.append(cls(client=client, board_id=board["_id"]))
        return instances

    def list_custom_fields(self, regex_filter=".*") -> list[Customfield]:
        """
        List all (matching) custom field
        :param regex_filter: Regex filter that will be applied to the search.
        :return: Instances of class Customfield
        """
        all_custom_fields = Customfield.from_list(
            parent_board=self, data=self.__get_all_custom_fields()
        )
        return [field for field in all_custom_fields if re.search(regex_filter, field.name)]

    def get_labels(self, regex_filter=".*") -> list[Label]:
        """
        Get all (matching) labels
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of labels
        """
        all_labels = Label.from_list(parent_board=self, data=self.__raw_data.get("labels", []))
        return [label for label in all_labels if re.search(regex_filter, label.name)]

    def get_lists(self, regex_filter=".*") -> list[WekanList]:
        """
        Get all (matching) lists
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of lists
        """
        all_lists = WekanList.from_list(parent_board=self, data=self.__get_all_lists())
        return [w_list for w_list in all_lists if re.search(regex_filter, w_list.title)]

    def list_swimlanes(self, regex_filter=".*") -> list[Swimlane]:
        """
        List all (matching) swimlanes
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of swimlanes
        """
        all_swimlanes = Swimlane.from_list(parent_board=self, data=self.__get_all_swimlanes())
        return [swimlane for swimlane in all_swimlanes if re.search(regex_filter, swimlane.title)]

    def list_integrations(self, regex_filter=".*") -> list[Integration]:
        """
        List all (matching) integrations
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of integrations
        """
        all_integrations = Integration.from_list(
            parent_board=self, data=self.__get_all_integrations()
        )
        return [
            integration
            for integration in all_integrations
            if re.search(regex_filter, integration.title)
        ]

    def get_swimlane_by_id(self, swimlane_id: str) -> Swimlane:
        """
        Get a single swimlane by id
        :param swimlane_id: id of the swimlane to fetch data from
        :return: Instance of type Swimlane
        """
        response = self.client.fetch_json(f"/api/boards/{self.id}/swimlanes/{swimlane_id}")
        return Swimlane.from_dict(parent_board=self, data=response)

    def get_list_by_id(self, list_id: str) -> WekanList:
        """
        Get a single list by id
        :param list_id: id of the list to fetch data from
        :return: Instance of type WekanList
        """
        response = self.client.fetch_json(f"/api/boards/{self.id}/lists/{list_id}")
        return WekanList.from_dict(parent_board=self, data=response)

    def get_integration_by_id(self, integration_id: str) -> Integration:
        """
        Get a single Integration by id
        :param integration_id: id of the integration to fetch data from
        :return: Instance of type List
        """
        response = self.client.fetch_json(f"/api/boards/{self.id}/integrations/{integration_id}")
        return Integration.from_dict(parent_board=self, data=response)

    def get_custom_field_by_id(self, custom_field_id: str) -> Customfield:
        """
        Get a single CustomField by id
        :param custom_field_id: id of the customfield to fetch data from
        :return: Instance of type Customfield
        """
        response = self.client.fetch_json(f"/api/boards/{self.id}/custom-fields/{custom_field_id}")
        return Customfield.from_dict(parent_board=self, data=response)

    def __get_all_custom_fields(self) -> list:
        """
        Get all custom fields by calling the API according to
        https://wekan.github.io/api/v7.42/#get_all_custom_fields
        :return: All custom field instances as list
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/custom-fields")

    def __get_all_lists(self) -> list:
        """
        Get all lists by calling the API according to
        https://wekan.github.io/api/v7.42/#get_all_lists
        :return: All lists as list
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/lists")

    def __get_all_swimlanes(self) -> list:
        """
        Get all swimlanes by calling the API according to
        https://wekan.github.io/api/v7.42/#get_all_swimlanes
        :return: All swimlanes as list
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/swimlanes")

    def __get_all_integrations(self) -> list:
        """
        Get all integrations by calling the API according to
        https://wekan.github.io/api/v7.42/#get_integration
        :return: All integrations as list
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/integrations")

    def create_list(self, title: str, position: int = None) -> WekanList:
        """
        Creates a new list instance.
        :param title: Name of the new list
        :param position: The position of the list in the board
        :return: Instance of Class WekanList
        """
        payload = {"title": title}
        if position:
            payload["sort"] = position
        response = self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/lists", http_method="POST", payload=payload
        )
        return WekanList.from_dict(parent_board=self, data=response)

    def add_swimlane(self, title: str) -> Swimlane:
        """
        Creates a new swimlane instance according to https://wekan.github.io/api/v7.42/#new_swimlane
        :param title: Name of the new swimlane
        :return: Instance of Class Swimlane
        """
        payload = {"title": title}
        response = self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/swimlanes",
            http_method="POST",
            payload=payload,
        )
        return Swimlane.from_dict(parent_board=self, data=response)

    def add_integration(self, url: str) -> Integration:
        """
        Creates a new integration instance according to
        https://wekan.github.io/api/v7.42/#new_integration
        :param url: the URL of the integration
        :return: Instance of Class Integration
        """
        payload = {"url": url}
        response = self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/integrations",
            http_method="POST",
            payload=payload,
        )
        return Integration.from_dict(parent_board=self, data=response)

    def add_custom_field(
        self,
        name: str,
        field_type: str,
        show_on_card: bool,
        automatically_on_card: bool,
        show_label_on_minicard: bool,
        show_sum_at_top_of_list: bool,
        settings=dict,
    ) -> Customfield:
        """
        Creates a new customfield instance according to
        https://wekan.github.io/api/v7.42/#new_custom_field
        :param name: Name of the new custom field.
        :param field_type: Type of field. See also allowed_fields.
        :param show_on_card: Determines if the custom field should be placed on card.
        :param automatically_on_card: Determines if the custom field should be
        placed automatically on card.
        :param show_label_on_minicard: Determines if the custom field should be
        showed on the mini card.
        :param show_sum_at_top_of_list: Determines if summary of all values should
        be placed on top of the list.
        :param settings: Setting to apply to custom field.
        :return: Instance of Class Customfield
        """
        allowed_fields = [
            "text",
            "number",
            "date",
            "dropdown",
            "currency",
            "checkbox",
            "stringtemplate",
        ]
        assert field_type in allowed_fields, f"field_type not in {allowed_fields}"
        show_sum_at_top_of_list = show_sum_at_top_of_list if field_type == "currency" else False

        payload = {
            "name": name,
            "type": field_type,
            "settings": settings,
            "showOnCard": show_on_card,
            "automaticallyOnCard": automatically_on_card,
            "showLabelOnMiniCard": show_label_on_minicard,
            "showSumAtTopOfList": show_sum_at_top_of_list,
        }
        response = self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/custom-fields",
            http_method="POST",
            payload=payload,
        )
        return Customfield.from_dict(parent_board=self, data=response)

    def delete(self) -> None:
        """
        Delete this board instance according to https://wekan.github.io/api/v7.42/#delete_board
        :return: None
        """
        self.client.fetch_json(f"/api/boards/{self.id}", http_method="DELETE")

    def update(
        self,
        title: str = None,
        description: str = None,
        color: str = None,
        permission: str = None,
    ) -> Board:
        """
        Update board properties.
        """
        payload = {}
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        if color:
            payload["color"] = color
        if permission:
            payload["permission"] = permission

        if payload:
            self.client.fetch_json(f"/api/boards/{self.id}", http_method="PUT", payload=payload)
            # Refresh data
            self.__init__(self.client, self.id)
        return self

    def archive(self) -> None:
        """
        Archive this board.
        """
        self.client.fetch_json(f"/api/boards/{self.id}/archive", http_method="POST")
        self.archived = True

    def restore(self) -> None:
        """
        Restore this board from archive.
        """
        self.client.fetch_json(f"/api/boards/{self.id}/restore", http_method="POST")
        self.archived = False

    def export(self) -> dict:
        """
        Export the instance Board according to https://wekan.github.io/api/v7.42/#export
        :return: Export of the board in dict format.
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/export")

    def get_members(self) -> list:
        """
        Get board members.
        """
        return self.client.fetch_json(f"/api/boards/{self.id}/members")

    def add_label(self, name: str, color: str) -> dict:
        """
        Create a new Label instance according to https://wekan.github.io/api/v7.42/#add_board_label
        """
        payload = {"name": name, "color": color}
        return self.client.fetch_json(
            f"/api/boards/{self.id}/labels", http_method="POST", payload=payload
        )

    def add_member(self, user_id: str, role: str = "normal") -> dict:
        """
        Add member to board.
        :param user_id: ID of user to add as member to the board.
        :param role: Role of the user. Can be "admin", "normal", "no-comments", "comment-only".
        """
        is_admin = role == "admin"
        # is_normal = role == "normal"  # Not a real flag in the API
        is_no_comments = role == "no-comments"
        is_comment_only = role == "comment-only"

        payload = {
            "action": "add",
            "isAdmin": is_admin,
            "isNoComments": is_no_comments,
            "isCommentOnly": is_comment_only,
        }
        return self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/members/{user_id}/add",
            http_method="POST",
            payload=payload,
        )

    def remove_member(self, user_id: str) -> None:
        """
        Remove a member from a board according to
        https://wekan.github.io/api/v7.42/#remove_board_member
        :param user_id: ID of user that will be removed as member of the board.
        :return: None
        """
        self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/members/{user_id}/remove",
            http_method="POST",
            payload={"action": "remove"},
        )

    def change_member_permission(
        self, user_id: str, is_admin: bool, is_no_comments: bool, is_comments_only: bool
    ) -> None:
        """
        Change the board member permission according to
        https://wekan.github.io/api/v7.42/#set_board_member_permission
        :param user_id: ID of user that permissions need to change.
        :param is_admin: Defines if the user an admin of the board
        :param is_no_comments: Defines if user is allowed to comment (only)
        :param is_comments_only: Defines if user is allowed to comment (only)
        :return: None
        """
        payload = {
            "isAdmin": is_admin,
            "isNoComments": is_no_comments,
            "isCommentOnly": is_comments_only,
        }
        self.client.fetch_json(
            uri_path=f"/api/boards/{self.id}/members/{user_id}",
            http_method="POST",
            payload=payload,
        )
