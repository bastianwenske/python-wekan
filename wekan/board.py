from __future__ import annotations

import re

from wekan.base import WekanBase
from wekan.customfield import Customfield
from wekan.integration import Integration
from wekan.label import Label
from wekan.swimlane import Swimlane
from wekan.wekan_list import List


class Board(WekanBase):
    def __init__(self, client, board_id: str) -> None:
        """ Reference to a Wekan board. """
        super().__init__()
        self.client = client
        self.id = board_id

        self.__raw_data = self.client.fetch_json(f'/api/boards/{self.id}')
        self.title = self.__raw_data['title']
        self.slug = self.__raw_data.get('slug', '')
        self.archived = self.__raw_data['archived']
        self.stars = self.__raw_data['stars']
        self.members = self.__raw_data['members']
        self.created_at = self.client.parse_iso_date(self.__raw_data['createdAt'])
        self.modified_at = self.client.parse_iso_date(self.__raw_data['modifiedAt'])
        self.permission = self.__raw_data['permission']
        self.color = self.__raw_data['color']
        self.subtasks_default_board_id = self.__raw_data['subtasksDefaultBoardId']
        self.subtasks_default_list_id = self.__raw_data['subtasksDefaultListId']
        self.allows_card_counterList = self.__raw_data['allowsCardCounterList']
        self.allows_board_member_list = self.__raw_data['allowsBoardMemberList']
        self.date_settings_default_board_id = self.__raw_data['dateSettingsDefaultBoardId']
        self.date_settings_default_list_id = self.__raw_data['dateSettingsDefaultListId']
        self.allow_subtasks = self.__raw_data['allowsSubtasks']
        self.allows_attachments = self.__raw_data['allowsAttachments']
        self.allows_checklists = self.__raw_data['allowsChecklists']
        self.allows_comments = self.__raw_data['allowsComments']
        self.allows_description_title = self.__raw_data['allowsDescriptionTitle']
        self.allows_description_text = self.__raw_data['allowsDescriptionText']
        self.allows_description_text_on_minicard = self.__raw_data['allowsDescriptionTextOnMinicard']
        self.allows_card_number = self.__raw_data['allowsCardNumber']
        self.allows_activities = self.__raw_data['allowsActivities']
        self.allows_labels = self.__raw_data['allowsLabels']
        self.allows_creator = self.__raw_data['allowsCreator']
        self.allows_assignee = self.__raw_data['allowsAssignee']
        self.allows_members = self.__raw_data['allowsMembers']
        self.allows_requested_by = self.__raw_data['allowsRequestedBy']
        self.allows_card_sorting_by_number = self.__raw_data['allowsCardSortingByNumber']
        self.allows_show_lists = self.__raw_data['allowsShowLists']
        self.allows_assigned_by = self.__raw_data['allowsAssignedBy']
        self.allows_received_date = self.__raw_data['allowsReceivedDate']
        self.allows_start_date = self.__raw_data['allowsStartDate']
        self.allows_end_date = self.__raw_data['allowsEndDate']
        self.allows_due_date = self.__raw_data['allowsDueDate']
        self.present_parent_task = self.__raw_data['presentParentTask']
        self.is_overtime = self.__raw_data['isOvertime']
        self.type = self.__raw_data['type']
        self.sort = self.__raw_data['sort']

    def __repr__(self) -> str:
        return f"<Board (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(cls, client, data: dict, ) -> Board:
        """
        Creates an instance of class Customfield by using the API-Response of Customfield creation.
        :param client: Instance of the wekan api client
        :param data: Response of CustomField creation
        :return: Instance of class CustomField
        """
        return cls(client=client, board_id=data['_id'])

    @classmethod
    def from_list(cls, client, data: dict) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param client: Instance of the wekan api client
        :param data: Responses of GET Boards
        :return Instances of class Board
        :rtype list
        """
        instances = []
        for board in data:
            instances.append(cls(client=client, board_id=board['_id']))
        return instances

    def list_custom_fields(self, regex_filter='.*') -> list:
        """
        List all (matching) custom field
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of users
        """
        all_custom_fields = Customfield.from_list(parent_board=self, data=self.__get_all_custom_fields())
        return [field for field in all_custom_fields if re.search(regex_filter, field.name)]

    def list_labels(self, regex_filter='.*') -> list:
        """
        List all (matching) labels
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of labels
        """
        all_labels = Label.from_list(parent_board=self, data=self.__raw_data.get('labels', []))
        return [label for label in all_labels if re.search(regex_filter, label.title)]

    def list_lists(self, regex_filter='.*') -> list:
        """
        List all (matching) labels
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of lists
        """
        all_lists = List.from_list(parent_board=self, data=self.__get_all_lists())
        return [w_list for w_list in all_lists if re.search(regex_filter, w_list.title)]

    def list_swimlanes(self, regex_filter='.*') -> list:
        """
        List all (matching) swimlanes
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of swimlanes
        """
        all_swimlanes = Swimlane.from_list(parent_board=self, data=self.__get_all_swimlanes())
        return [swimlane for swimlane in all_swimlanes if re.search(regex_filter, swimlane.title)]

    def list_integrations(self, regex_filter='.*') -> list:
        """
        List all (matching) integrations
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of integrations
        """
        all_integrations = Integration.from_list(parent_board=self, data=self.__get_all_integrations())
        return [integration for integration in all_integrations if re.search(regex_filter, integration.title)]

    def get_swimlane_by_id(self, swimlane_id: str) -> Swimlane:
        """
        Get a single swimlane by id
        :param swimlane_id: id of the swimlane to fetch data from
        :return: Instance of type Swimlane
        """
        response = self.client.fetch_json(f'/api/boards/{self.id}/swimlanes/{swimlane_id}')
        return Swimlane.from_dict(parent_board=self, data=response)

    def get_list_by_id(self, list_id: str) -> List:
        """
        Get a single list by id
        :param list_id: id of the list to fetch data from
        :return: Instance of type List
        """
        response = self.client.fetch_json(f'/api/boards/{self.id}/lists/{list_id}')
        return List.from_dict(parent_board=self, data=response)

    def get_integration_by_id(self, integration_id: str) -> Integration:
        """
        Get a single Integration by id
        :param integration_id: id of the integration to fetch data from
        :return: Instance of type List
        """
        response = self.client.fetch_json(f'/api/boards/{self.id}/integrations/{integration_id}')
        return Integration.from_dict(parent_board=self, data=response)

    def get_custom_field_by_id(self, custom_field_id: str) -> Customfield:
        """
        Get a single CustomField by id
        :param custom_field_id: id of the customfield to fetch data from
        :return: Instance of type Customfield
        """
        response = self.client.fetch_json(f'/api/boards/{self.id}/custom-fields/{custom_field_id}')
        return Customfield.from_dict(parent_board=self, data=response)

    def __get_all_custom_fields(self) -> list:
        """
        Get all custom fields by calling the API according to https://wekan.github.io/api/v6.22/#get_all_custom_fields
        :return: All custom field instances as list
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/custom-fields')

    def __get_all_lists(self) -> list:
        """
        Get all lists by calling the API according to https://wekan.github.io/api/v6.22/#get_all_lists
        :return: All lists as list
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/lists')

    def __get_all_swimlanes(self) -> list:
        """
        Get all swimlanes by calling the API according to https://wekan.github.io/api/v6.22/#get_all_swimlanes
        :return: All swimlanes as list
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/swimlanes')

    def __get_all_integrations(self) -> list:
        """
        Get all integrations by calling the API according to https://wekan.github.io/api/v6.22/#get_integration
        :return: All integrations as list
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/integrations')

    def add_list(self, title: str) -> List:
        """
        Creates a new list instance according to https://wekan.github.io/api/v6.22/#new_list
        :param title: Name of the new list
        :return: Instance of Class List
        """
        payload = {"title": title}
        response = self.client.fetch_json(uri_path=f'/api/boards/{self.id}/lists',
                                          http_method="POST", payload=payload)
        return List.from_dict(parent_board=self, data=response)

    def add_swimlane(self, title: str) -> Swimlane:
        """
        Creates a new swimlane instance according to https://wekan.github.io/api/v6.22/#new_swimlane
        :param title: Name of the new swimlane
        :return: Instance of Class Swimlane
        """
        payload = {"title": title}
        response = self.client.fetch_json(uri_path=f'/api/boards/{self.id}/swimlanes',
                                          http_method="POST", payload=payload)
        return Swimlane.from_dict(parent_board=self, data=response)

    def add_integration(self, url: str) -> Integration:
        """
        Creates a new integration instance according to https://wekan.github.io/api/v6.22/#new_integration
        :param url: the URL of the integration
        :return: Instance of Class Integration
        """
        payload = {"url": url}
        response = self.client.fetch_json(uri_path=f'/api/boards/{self.id}/integrations',
                                          http_method="POST", payload=payload)
        return Integration.from_dict(parent_board=self, data=response)

    def add_custom_field(self, name: str, field_type: str, show_on_card: bool,
                         automatically_on_card: bool, show_label_on_minicard: bool,
                         show_sum_at_top_of_list: bool, settings=dict) -> Customfield:
        """
        Creates a new customfield instance according to https://wekan.github.io/api/v6.22/#new_custom_field
        :param name: Name of the new custom field.
        :param field_type: Type of field. See also allowed_fields.
        :param show_on_card: Determines if the custom field should be placed on card.
        :param automatically_on_card: Determines if the custom field should be placed automatically on card.
        :param show_label_on_minicard: Determines if the custom field should be showed on the mini card.
        :param show_sum_at_top_of_list: Determines if summary of all values should be placed on top of the list.
        :param settings: Setting to apply to custom field.
        :return: Instance of Class Customfield
        """
        allowed_fields = ["text", "number", "date", "dropdown", "currency", "checkbox", "stringtemplate"]
        assert field_type in allowed_fields, f"field_type not in {allowed_fields}"
        show_sum_at_top_of_list = show_sum_at_top_of_list if field_type == "currency" else False

        payload = {
            "name": name,
            "type": field_type,
            "settings": settings,
            "showOnCard": show_on_card,
            "automaticallyOnCard": automatically_on_card,
            "showLabelOnMiniCard": show_label_on_minicard,
            "showSumAtTopOfList": show_sum_at_top_of_list
        }
        response = self.client.fetch_json(uri_path=f'/api/boards/{self.id}/custom-fields',
                                          http_method="POST", payload=payload)
        return Customfield.from_dict(parent_board=self, data=response)

    def delete(self) -> None:
        """
        Delete this board instance according to https://wekan.github.io/api/v6.22/#delete_board
        :return: None
        """
        self.client.fetch_json(f'/api/boards/{self.id}', http_method="DELETE")

    def export(self) -> dict:
        """
        Export the instance Board according to https://wekan.github.io/api/v6.22/#export
        :return: Export of the board in dict format.
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/export')

    def add_label(self):
        """
        Create a new Label instance according to https://wekan.github.io/api/v6.22/#add_board_label
        Currently, there is a problem when api handles the request:
        Api docs do not match with actual behaviour.
        see also: https://wekan.github.io/api/v6.22/?shell#add_board_label
        """
        raise NotImplementedError

    def add_member(self, user_id: str, is_admin: bool, is_no_comments: bool, is_comments_only: bool) -> None:
        """
        Add a member to a board according to https://wekan.github.io/api/v6.22/#add_board_member
        :param user_id: ID of user to add as member to the board.
        :param is_admin: Defines if the user an admin of the board
        :param is_no_comments: Defines if user is allowed to comment (only)
        :param is_comments_only: Defines if user is allowed to comment (only)
        :return: None
        """
        payload = {
            "action": "add",
            "isAdmin": is_admin,
            "isNoComments": is_no_comments,
            "isCommentOnly": is_comments_only
        }
        self.client.fetch_json(uri_path=f'/api/boards/{self.id}/members/{user_id}/add',
                               http_method="POST", payload=payload)

    def remove_member(self, user_id: str) -> None:
        """
        Remove a member from a board according to https://wekan.github.io/api/v6.22/#remove_board_member
        :param user_id: ID of user that will be removed as member of the board.
        :return: None
        """
        self.client.fetch_json(uri_path=f'/api/boards/{self.id}/members/{user_id}/remove',
                               http_method="POST", payload={"action": "remove"})

    def change_member_permission(self, user_id: str, is_admin: bool, is_no_comments: bool,
                                 is_comments_only: bool) -> None:
        """
        Change the board member permission according to https://wekan.github.io/api/v6.22/#set_board_member_permission
        :param user_id: ID of user that permissions need to change.
        :param is_admin: Defines if the user an admin of the board
        :param is_no_comments: Defines if user is allowed to comment (only)
        :param is_comments_only: Defines if user is allowed to comment (only)
        :return: None
        """
        payload = {
            "isAdmin": is_admin,
            "isNoComments": is_no_comments,
            "isCommentOnly": is_comments_only
        }
        self.client.fetch_json(uri_path=f'/api/boards/{self.id}/members/{user_id}',
                               http_method="POST", payload=payload)
