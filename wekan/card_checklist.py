from __future__ import annotations
from wekan.base import WekanBase
from wekan.card_checklist_item import CardChecklistItem


class CardChecklist(WekanBase):
    def __init__(self, parent_card, checklist_id: str) -> None:
        """ Reference to a Wekan Card Checklist """
        super().__init__()
        self.card = parent_card
        self.id = checklist_id
        self.__fetch_all_attributes()

    def __fetch_all_attributes(self) -> None:
        """
        Fetch and set all instance attributes.
        :return: None
        """
        uri = f'/api/boards/{self.card.list.board.id}/cards/{self.card.id}/checklists/{self.id}'
        data = self.card.list.board.client.fetch_json(uri)
        self.title = data['title']
        self.sort = data['sort']
        self.createdAt = self.card.list.board.client.parse_iso_date(data['createdAt'])
        self.modified_at = self.card.list.board.client.parse_iso_date(data['modifiedAt'])
        self.items = CardChecklistItem.from_list(parent_checklist=self, data=data['items'])

    def __repr__(self) -> str:
        return f"<CardChecklist (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(cls, parent_card, data: dict) -> CardChecklist:
        """
        Creates an instance of class CardChecklist by using the API-Response of CardChecklist GET.
        :param parent_card: Instance of Class Card pointing to the current Card of this Checklist
        :param data: Response of CardChecklist GET.
        :return: Instance of class CardChecklist
        """
        return cls(parent_card=parent_card, checklist_id=data['_id'])

    @classmethod
    def from_list(cls, parent_card, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_card: Instance of Class Card pointing to the current Card of this Checklist
        :param data: Response of CardChecklist GET.
        :return: Instances of class CardChecklist
        """
        instances = []
        for checklist in data:
            instances.append(cls(parent_card=parent_card, checklist_id=checklist['_id']))
        return instances

    def edit(self, data: dict) -> None:
        """
        Edit the current instance by sending a PUT Request to the API.
        Currently, this is not supported by API. See also: https://wekan.github.io/api/v2.55/#wekan-rest-api-checklists
        """
        raise NotImplementedError

    def delete(self) -> None:
        """
        Delete the Card Checklist instance according to https://wekan.github.io/api/v2.55/#delete_checklist
        :return: None
        """
        uri = f'/api/boards/{self.board.id}/cards/{self.card.id}/checklists/{self.id}'
        self.card.list.board.client.fetch_json(uri, http_method="DELETE")
