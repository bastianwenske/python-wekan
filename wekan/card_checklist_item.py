from __future__ import annotations

from wekan.base import WekanBase


class CardChecklistItem(WekanBase):
    def __init__(self, parent_checklist, item_id: str, title: str, is_finished: bool) -> None:
        """ Reference to a Wekan CardChecklistItem """
        super().__init__()
        self.checklist = parent_checklist
        self.id = item_id
        self.title = title
        self.is_finished = is_finished

        uri = f'/api/boards/{self.checklist.card.list.board.id}/cards/{self.checklist.card.id}/' \
              f'checklists/{self.checklist.id}/items/{self.id}'
        data = self.checklist.card.list.board.client.fetch_json(uri)
        self.sort = data['sort']

    def __repr__(self) -> str:
        return f"<CardChecklistItem (id: {self.id}, title: {self.title}, is_finished: {self.is_finished})>"

    @classmethod
    def from_dict(cls, parent_checklist, data: dict) -> CardChecklistItem:
        """
        Creates an instance of class CardChecklist by using the API-Response of CardChecklist GET.
        :param parent_checklist: Instance of Class CardChecklist pointing to the current Checklist of this ChecklistItem
        :param data: Response of CardChecklist GET.
        :return: Instance of class CardChecklistItem
        """
        return cls(parent_checklist=parent_checklist, item_id=data['_id'],
                   title=data['title'], is_finished=data['isFinished'])

    @classmethod
    def from_list(cls, parent_checklist, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_checklist: Instance of Class CardChecklist pointing to the current Checklist of this ChecklistItem
        :param data: Response of CardChecklist GET.
        :return: Instances of class CardChecklist
        """
        instances = []
        for item in data:
            instances.append(cls(parent_checklist=parent_checklist, item_id=item['_id'],
                                 title=item['title'], is_finished=item['isFinished']))
        return instances

    def edit(self, is_finished=None, title=None) -> None:
        """
        Edit the current instance by sending a PUT Request to the API
        according to https://wekan.github.io/api/v6.22/#edit_checklist_item
        :param is_finished: is the item checked?
        :param title: the new text of the item
        :return: None
        """
        payload = {}
        if is_finished:
            payload["isFinished"] = is_finished
        if title:
            payload["title"] = title

        uri = f'/api/boards/{self.checklist.card.list.board.id}/cards/{self.checklist.card.id}/' \
              f'checklists/{self.checklist.id}/items/{self.id}'
        self.checklist.card.list.board.client.fetch_json(uri, payload=payload, http_method="PUT")

    def mark_as_finished(self) -> None:
        """
        Mark this instance as finished.
        :return: None
        """
        self.edit(is_finished=True)

    def change_title(self, new_title) -> None:
        """
        Set a new title for this instance.
        :param new_title: The new title.
        :return: None
        """
        self.edit(title=new_title)

    def delete(self) -> None:
        """
        Delete the Card Checklist instance according to https://wekan.github.io/api/v6.22/#delete_checklist_item
        :return: None
        """
        uri = f'/api/boards/{self.checklist.card.board.id}/cards/{self.checklist.card.id}/' \
              f'checklists/{self.checklist.id}/items/{self.id}'
        self.checklist.card.board.client.fetch_json(uri, http_method="DELETE")
