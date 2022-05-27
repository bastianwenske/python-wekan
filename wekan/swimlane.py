from __future__ import annotations

from wekan.base import WekanBase


class Swimlane(WekanBase):
    def __init__(self, parent_board, swimlane_id: str) -> None:
        """ Reference to a Wekan Swimlane """
        super().__init__()
        self.board = parent_board
        self.id = swimlane_id

        data = self.board.client.fetch_json(f'/api/boards/{self.board.id}/swimlanes/{self.id}')
        self.title = data['title']
        self.archived = data['archived']
        self.created_at = self.board.client.parse_iso_date(data['createdAt'])
        self.updated_at = self.board.client.parse_iso_date(data['updatedAt'])
        self.sort = data.get('sort')
        self.color = data.get('color', '')
        self.type = data['type']

    def __repr__(self) -> str:
        return f"<Swimlane (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(cls, parent_board, data: dict) -> Swimlane:
        """
        Creates an instance of class Swimlane by using the API-Response of Swimlane GET.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of Swimlane GET.
        :return: Instance of class Swimlane
        """
        return cls(parent_board=parent_board, swimlane_id=data['_id'])

    @classmethod
    def from_list(cls, parent_board, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Responses of Swimlane GET.
        :return: Instances of class Swimlane
        """
        instances = []
        for swimlane in data:
            instances.append(cls(parent_board=parent_board, swimlane_id=swimlane['_id']))
        return instances

    def delete(self) -> None:
        """
        Delete the Swimlane instance according to https://wekan.github.io/api/v6.22/#get_swimlane
        :return: None
        """
        self.board.client.fetch_json(f'/api/boards/{self.board.id}/swimlanes/{self.id}', http_method="DELETE")
