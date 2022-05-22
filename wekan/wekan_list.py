from __future__ import annotations
from wekan.base import WekanBase
from wekan.card import Card
from wekan.swimlane import Swimlane


class List(WekanBase):
    def __init__(self, parent_board, list_id: int) -> None:
        """ Reference to a Wekan List. """
        super().__init__()
        self.board = parent_board
        self.id = list_id
        self.__fetch_all_attributes()
        self.cards = Card.from_list(parent_list=self, data=self.get_all_cards_on_list())

    def __fetch_all_attributes(self) -> None:
        """
        Fetch and set all instance attributes.
        :return: None
        """
        data = self.board.client.fetch_json(f'/api/boards/{self.board.id}/lists/{self.id}')
        self.title = data['title']
        self.archived = data['archived']
        self.swimlane_id = data['swimlaneId']
        self.created_at = self.board.client.parse_iso_date(data['createdAt'])
        self.updated_at = self.board.client.parse_iso_date(data['updatedAt'])
        self.sort = data['sort']
        self.wip_limit = data['wipLimit']
        self.color = data.get('color', '')
        data_cc = self.board.client.fetch_json(f'/api/boards/{self.board.id}/lists/{self.id}/cards_count')
        self.cards_count = data_cc['list_cards_count']

    def __repr__(self) -> str:
        return f"<List (id: {self.id}, title: {self.title})>"

    def get_all_cards_on_list(self) -> list:
        """
        Get all cards by calling the API according to https://wekan.github.io/api/v2.55/#get_list
        :return: All cards
        """
        return self.board.client.fetch_json(f'/api/boards/{self.board.id}/lists/{self.id}/cards')

    @classmethod
    def from_dict(cls, parent_board, data: dict) -> List:
        """
        Creates an instance of class List by using the API-Response of List creation.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of List creation.
        :return: Instance of class List
        """
        return cls(parent_board=parent_board, list_id=data['_id'])

    @classmethod
    def from_list(cls, parent_board, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of List creation.
        :return: Instances of class List
        """
        instances = []
        for wekan_list in data:
            instances.append(cls(parent_board=parent_board, list_id=wekan_list['_id']))
        return instances

    def delete(self) -> None:
        """
        Delete the List instance.
        :return: None
        """
        self.board.client.fetch_json(f'/api/boards/{self.board.id}/lists/{self.id}',
                                     http_method="DELETE")

    def add_card(self, title: str, swimlane: Swimlane, members="", description="") -> Card:
        """
        Creates a new card instance according to https://wekan.github.io/api/v2.55/#new_card
        :param title: Title of the new card.
        :param swimlane: Swimlane ID of the new card.
        :param members: Members of the new card.
        :param description: Description of the new card.
        :return: Instance of type Card
        """
        payload = {
            'title': title,
            'authorId': self.board.client.user_id,
            'members': members,
            'description': description,
            'swimlaneId': swimlane.id
        }
        response = self.board.client.fetch_json(uri_path=f'/api/boards/{self.board.id}/lists/{self.id}/cards',
                                                http_method="POST", payload=payload)
        instance = Card.from_dict(parent_board=self.board, parent_list=self, data=response)
        self.cards.append(instance)
        return instance
