from __future__ import annotations
from wekan.base import WekanBase
from wekan.label import Label
from wekan.customfield import Customfield
from wekan.wekan_list import List
from wekan.swimlane import Swimlane


class Board(WekanBase):
    def __init__(self, client, board_id=None) -> None:
        """ Reference to a Wekan board. """
        super().__init__()
        self.client = client
        self.id = board_id
        self.__fetch_all()

    def __fetch_all(self) -> None:
        """
        Fetch and set all instance attributes.
        :return: None
        """
        data = self.client.fetch_json(f'/api/boards/{self.id}')
        self.title = data['title']
        self.slug = data.get('slug', '')
        self.archived = data['archived']
        self.stars = data['stars']
        self.members = data['members']
        self.created_at = self.client.parse_iso_date(data['createdAt'])
        self.modified_at = self.client.parse_iso_date(data['modifiedAt'])
        self.permission = data['permission']
        self.color = data['color']
        self.subtasks_default_board_id = data['subtasksDefaultBoardId']
        self.subtasks_default_list_id = data['subtasksDefaultListId']
        self.allows_card_counterList = data['allowsCardCounterList']
        self.allows_board_member_list = data['allowsBoardMemberList']
        self.date_settings_default_board_id = data['dateSettingsDefaultBoardId']
        self.date_settings_default_list_id = data['dateSettingsDefaultListId']
        self.allow_subtasks = data['allowsSubtasks']
        self.allows_attachments = data['allowsAttachments']
        self.allows_checklists = data['allowsChecklists']
        self.allows_comments = data['allowsComments']
        self.allows_description_title = data['allowsDescriptionTitle']
        self.allows_description_text = data['allowsDescriptionText']
        self.allows_description_text_on_minicard = data['allowsDescriptionTextOnMinicard']
        self.allows_card_number = data['allowsCardNumber']
        self.allows_activities = data['allowsActivities']
        self.allows_labels = data['allowsLabels']
        self.allows_creator = data['allowsCreator']
        self.allows_assignee = data['allowsAssignee']
        self.allows_members = data['allowsMembers']
        self.allows_requested_by = data['allowsRequestedBy']
        self.allows_card_sorting_by_number = data['allowsCardSortingByNumber']
        self.allows_show_lists = data['allowsShowLists']
        self.allows_assigned_by = data['allowsAssignedBy']
        self.allows_received_date = data['allowsReceivedDate']
        self.allows_start_date = data['allowsStartDate']
        self.allows_end_date = data['allowsEndDate']
        self.allows_due_date = data['allowsDueDate']
        self.present_parent_task = data['presentParentTask']
        self.is_overtime = data['isOvertime']
        self.type = data['type']
        self.sort = data['sort']
        self.custom_fields = Customfield.from_list(parent_board=self, data=self.get_all_custom_fields())
        self.labels = Label.from_list(parent_board=self, data=data.get('labels', []))
        self.lists = List.from_list(parent_board=self, data=self.get_all_lists())
        self.swimlanes = Swimlane.from_list(parent_board=self, data=self.get_all_swimlanes())

    def __repr__(self) -> str:
        return f"<Board (id: {self.id}, name: {self.title})>"

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

    def get_all_custom_fields(self) -> list:
        """
        Get all custom fields by calling the API according to https://wekan.github.io/api/v2.55/#get_all_custom_fields
        :return: All custom fields
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/custom-fields')

    def get_all_lists(self) -> list:
        """
        Get all lists by calling the API according to https://wekan.github.io/api/v2.55/#get_all_lists
        :return: All lists
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/lists')

    def get_all_swimlanes(self) -> list:
        """
        Get all swimlanes by calling the API according to https://wekan.github.io/api/v2.55/#get_all_swimlanes
        :return: All lists
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/swimlanes')

    def get_swimlane_by_title(self, title) -> Swimlane:
        """
        Get swimlane by title.
        :return: Instance of Swimlane
        """
        for swimlane in self.swimlanes:
            if title == swimlane.title:
                return swimlane

    def get_list_by_title(self, title) -> List:
        """
        Get list by title.
        :return: Instance of List
        """
        for wekan_list in self.lists:
            if title == wekan_list.title:
                return wekan_list

    def create_list(self, name: str) -> List:
        """
        Creates a new list instance according to https://wekan.github.io/api/v2.55/#new_list
        :param name: Name of the new list
        :return: Instance of Class List
        """
        payload = {"title": name}
        response = self.client.fetch_json(uri_path=f'/api/boards/{self.id}/lists',
                                          http_method="POST", payload=payload)
        instance = List.from_dict(parent_board=self, data=response)
        self.lists.append(instance)
        return instance

    def create_custom_field(self, name: str, field_type: str, show_on_card: bool,
                            automatically_on_card: bool, show_label_on_minicard: bool,
                            show_sum_at_top_of_list: bool, settings={}) -> Customfield:
        """
        Creates a new customfield instance according to https://wekan.github.io/api/v2.55/#get_custom_field
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
        instance = Customfield.from_dict(parent_board=self, data=response)
        self.custom_fields.append(instance)
        return instance

    def delete(self) -> None:
        """
        Delete this board instance according to https://wekan.github.io/api/v2.55/#delete_board
        :return: None
        """
        self.client.fetch_json(f'/api/boards/{self.id}', http_method="DELETE")

    def export(self) -> dict:
        """
        Export the instance Board according to https://wekan.github.io/api/v2.55/#export
        :return: Export of the board in dict format.
        """
        return self.client.fetch_json(f'/api/boards/{self.id}/export')

    def add_label(self):
        """
        Create a new Label instance according to https://wekan.github.io/api/v2.55/#add_board_label
        Currently, there is a problem when api handles the request:
        Api docs do not match with actual behaviour.
        see also: https://wekan.github.io/api/v2.55/?shell#add_board_label
        """
        raise NotImplementedError

    def add_member(self, user_id: str, is_admin: bool, is_no_comments: bool, is_comments_only: bool) -> None:
        """
        Add a member to a board according to https://wekan.github.io/api/v2.55/#add_board_member
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
        Remove a member from a board according to https://wekan.github.io/api/v2.55/#remove_board_member
        :param user_id: ID of user that will be removed as member of the board.
        :return: None
        """
        self.client.fetch_json(uri_path=f'/api/boards/{self.id}/members/{user_id}/remove',
                               http_method="POST", payload={"action": "remove"})

    def change_member_permission(self, user_id: str, is_admin: bool, is_no_comments: bool, is_comments_only: bool) -> None:
        """
        Change the board member permission according to https://wekan.github.io/api/v2.55/#set_board_member_permission
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
