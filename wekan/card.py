from __future__ import annotations

from datetime import date
import re

from wekan.base import WekanBase
from wekan.card_checklist import CardChecklist
from wekan.card_comment import CardComment


class Card(WekanBase):
    def __init__(self, parent_list, card_id: str) -> None:
        """ Reference to a Wekan Card """
        super().__init__()
        self.list = parent_list
        self.id = card_id

        uri = f'/api/boards/{self.list.board.id}/lists/{self.list.id}/cards/{self.id}'
        data = self.list.board.client.fetch_json(uri)
        self.title = data['title']
        self.members = data['members']
        self.label_ids = data['labelIds']
        self.custom_fields = data['customFields']
        self.sort = data['sort']
        self.swimlane_id = data['swimlaneId']
        self.card_number = data['cardNumber']
        self.archived = data['archived']
        self.parent_id = data['parentId']
        self.cover_id = data['coverId']
        self.created_at = self.list.board.client.parse_iso_date(data['createdAt'])
        self.modified_at = self.list.board.client.parse_iso_date(data['modifiedAt'])
        self.date_last_activity = self.list.board.client.parse_iso_date(data['dateLastActivity'])
        self.description = data['description']
        self.requested_by = data['requestedBy']
        self.assigned_by = data['assignedBy']
        self.assignees = data['assignees']
        self.spent_time = data['spentTime']
        self.is_overtime = data['isOvertime']
        self.subtask_sort = data['subtaskSort']
        self.linked_id = data['linkedId']
        self.vote = data['vote']
        self.poker = data['poker']
        self.target_id_gantt = data['targetId_gantt']
        self.link_type_gantt = data['linkType_gantt']
        self.link_id_gantt = data['linkId_gantt']
        try:
            self.due_at = self.list.board.client.parse_iso_date(data['dueAt'])
        except KeyError:
            self.due_at = None

    def __repr__(self) -> str:
        return f"<Card (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(cls, parent_list, data: dict) -> Card:
        """
        Creates an instance of class Card by using the API-Response of Card GET.
        :param parent_list: Instance of Class List pointing to the current Board
        :param data: Response of Card GET.
        :return: Instance of class Card
        """
        return cls(parent_list=parent_list, card_id=data['_id'])

    @classmethod
    def from_list(cls, parent_list, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_list: Instance of Class List pointing to the current Board
        :param data: Response of Card GET.
        :return: Instances of class Card
        """
        instances = []
        for card in data:
            instances.append(cls(parent_list=parent_list, card_id=card['_id']))
        return instances

    def __get_all_checklists(self) -> list:
        """
        Get all Checklists by calling the API according to https://wekan.github.io/api/v6.22/#get_all_checklists
        :return: All Checklists
        """
        return self.list.board.client.fetch_json(f'/api/boards/{self.list.board.id}/cards/{self.id}/checklists')

    def list_checklists(self, regex_filter='.*') -> list:
        """
        List all (matching) checklists
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of checklists
        """
        all_checklists = CardChecklist.from_list(parent_card=self, data=self.__get_all_checklists())
        return [checklist for checklist in all_checklists if re.search(regex_filter, checklist.title)]

    def __get_all_comments(self) -> list:
        """
        Get all Comments by calling the API according to https://wekan.github.io/api/v6.22/#get_all_comments
        :return: All Checklists
        """
        return self.list.board.client.fetch_json(f'/api/boards/{self.list.board.id}/cards/{self.id}/comments')

    def list_comments(self, author_id=None) -> list:
        """
        List all (matching) checklists
        :param author_id: author_id filter that will be applied to the search.
        :return: list of checklists
        """
        all_comments = CardComment.from_list(parent_card=self, data=self.__get_all_comments())
        if author_id:
            return [comment for comment in all_comments if author_id == comment.author_id]
        else:
            return all_comments

    def delete(self) -> None:
        """
        Delete the Card instance according to https://wekan.github.io/api/v6.22/#delete_card
        :return: API Response as type dict containing the id of the deleted card
        """
        uri = f'/api/boards/{self.list.board.id}/lists/{self.list.id}/cards/{self.id}'
        self.list.board.client.fetch_json(uri, http_method="DELETE")

    def add_checklist(self, title: str) -> CardChecklist:
        """
        Create a new CardChecklist instance according to https://wekan.github.io/api/v6.22/#new_checklist
        :param title: Title of the new checklist.
        :return: Instance of class CardChecklist
        """
        payload = {
            "title": title
        }
        uri = f'/api/boards/{self.list.board.id}/cards/{self.id}/checklists'
        response = self.list.board.client.fetch_json(uri_path=uri, http_method="POST", payload=payload)
        return CardChecklist.from_dict(parent_card=self, data=response)

    def add_comment(self, text: str) -> CardComment:
        """
        Create a new CardChecklist instance according to https://wekan.github.io/api/v6.22/#new_comment
        :param text: Text of the new comment.
        :return: Instance of class CardComment
        """
        payload = {
            "authorId": self.list.board.client.user_id,
            "comment": text
        }
        uri = f'/api/boards/{self.list.board.id}/cards/{self.id}/comments'
        response = self.list.board.client.fetch_json(uri, http_method="POST", payload=payload)
        return CardComment.from_dict(parent_card=self, data=response)

    def edit(self, title=None, new_list=None, author_id=None, description=None, color=None, label_ids=None,
             requested_by=None, assigned_by=None, received_at=None, start_at=None, due_at=None, end_at=None,
             spent_time=None, is_overtime=None, custom_fields=None, members=None, new_swimlane=None) -> None:
        """
        Edit the current instance by sending a PUT Request to the API
        according to https://wekan.github.io/api/v6.22/#edit_card
        :param title: the new title of the card
        :param new_list: instance of class List of the new list (move operation)
        :param author_id: change the owner of the card
        :param description: the new description of the card
        :param color: the new color of the card
        :param label_ids: the new list of label IDs attached to the card
        :param requested_by: the new requestedBy field of the card
        :param assigned_by: the new assignedBy field of the card
        :param received_at: the new receivedAt field of the card
        :param start_at: the new startAt field of the card
        :param due_at: the new dueAt field of the card
        :param end_at: the new endAt field of the card
        :param spent_time: the new spentTime field of the card
        :param is_overtime: the new isOverTime field of the card
        :param custom_fields: the new customFields value of the card
        :param members: the new list of member IDs attached to the card
        :param new_swimlane: instance of class Swimlane of the new swimlane (move operation)
        :return: None
        """
        payload = {}
        if title:
            payload['title'] = title
        if new_list:
            payload['listId'] = new_list.id
        if author_id:
            payload['authorId'] = author_id
        if description:
            payload['description'] = description
        if color:
            payload['color'] = color
        if label_ids:
            assert isinstance(label_ids, list)
            payload['labelIds'] = label_ids
        if requested_by:
            payload['requestedBy'] = requested_by
        if assigned_by:
            payload['assignedBy'] = assigned_by
        if received_at:
            assert isinstance(received_at, date)
            payload['receivedAt'] = received_at.isoformat()
        if start_at:
            assert isinstance(start_at, date)
            payload['startAt'] = start_at.isoformat()
        if due_at:
            assert isinstance(due_at, date)
            payload['dueAt'] = due_at.isoformat()
        if end_at:
            assert isinstance(end_at, date)
            payload['endAt'] = end_at.isoformat()
        if spent_time:
            assert isinstance(spent_time, int)
            payload['spentTime'] = spent_time
        if is_overtime:
            assert isinstance(is_overtime, bool)
            payload['isOverTime'] = is_overtime
        if custom_fields:
            payload['customFields'] = custom_fields
        if members:
            assert isinstance(members, list)
            payload['members'] = members
        if new_swimlane:
            payload['swimlaneId	'] = new_swimlane.id

        uri = f'/api/boards/{self.list.board.id}/lists/{self.list.id}/cards/{self.id}'
        self.list.board.client.fetch_json(uri, payload=payload, http_method="PUT")
