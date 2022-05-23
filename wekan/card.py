from __future__ import annotations

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
        Get all Checklists by calling the API according to https://wekan.github.io/api/v2.55/#get_all_checklists
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
        Get all Comments by calling the API according to https://wekan.github.io/api/v2.55/#get_all_comments
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

    def edit(self, data: dict) -> None:
        """
        Edit the current instance by sending a PUT Request to the API
        according to https://wekan.github.io/api/v2.55/#edit_card
        Then re-fetch all instance attributes.
        :param data: Changed fields as dict object. Example: {'title': 'changed title'}
        :return: API Response as type dict containing the id of the changed Card
        """
        uri = f'/api/boards/{self.list.board.id}/lists/{self.list.id}/cards/{self.id}'
        self.list.board.client.fetch_json(uri, payload=data, http_method="PUT")

    def delete(self) -> None:
        """
        Delete the Card instance according to https://wekan.github.io/api/v2.55/#delete_card
        :return: API Response as type dict containing the id of the deleted card
        """
        uri = f'/api/boards/{self.list.board.id}/lists/{self.list.id}/cards/{self.id}'
        self.list.board.client.fetch_json(uri, http_method="DELETE")

    def add_checklist(self, title: str) -> CardChecklist:
        """
        Create a new CardChecklist instance according to https://wekan.github.io/api/v2.55/#new_checklist
        :param title: Title of the new checklist.
        :return: Instance of class CardChecklist
        """
        payload = {
            "title": title
        }
        response = self.list.board.client.fetch_json(uri_path=f'/api/boards/{self.id}/cards/{self.id}/checklists',
                                                     http_method="POST", payload=payload)
        return CardChecklist.from_dict(parent_card=self, data=response)

    def add_comment(self, comment: str) -> CardComment:
        """
        Create a new CardChecklist instance according to https://wekan.github.io/api/v2.55/#new_comment
        :param comment: Text of the new comment.
        :return: Instance of class CardComment
        """
        payload = {
            "authorId": self.list.board.client.user_id,
            "comment": comment
        }
        uri = f'/api/boards/{self.list.board.id}/cards/{self.id}/comments'
        response = self.list.board.client.fetch_json(uri, http_method="POST", payload=payload)
        return CardComment.from_dict(parent_card=self, data=response)
