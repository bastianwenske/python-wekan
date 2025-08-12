from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from wekan.board import Board

import logging
import re

from wekan.base import WekanBase
from wekan.card import WekanCard


class WekanList(WekanBase):
    def __init__(self, parent_board: Board, list_id: str) -> None:
        """Reference to a Wekan List."""
        super().__init__()
        self.board = parent_board
        self.id = list_id

        data = self.board.client.fetch_json(f"/api/boards/{self.board.id}/lists/{self.id}")
        self.title = data["title"]
        self.archived = data["archived"]
        self.swimlane_id = data["swimlaneId"]
        self.created_at = self.board.client.parse_iso_date(data["createdAt"])
        self.updated_at = self.board.client.parse_iso_date(data["updatedAt"])
        try:
            self.sort = data["sort"]
        except Exception:
            logging.exception(
                "List lacks sort parameter! Is this a subtasks board?",
                "https://github.com/wekan/wekan/issues/5582",
            )
            logging.debug(list_id)
        self.wip_limit = data["wipLimit"]
        self.color = data.get("color", "")

        try:
            data_cc = self.board.client.fetch_json(
                f"/api/boards/{self.board.id}/lists/{self.id}/cards_count"
            )
            self.cards_count = data_cc["list_cards_count"]
        except Exception:
            logging.exception(
                "Failed getting cards_count, instance possibly too old (stable snap?)"
            )
            logging.debug(list_id)

    def __repr__(self) -> str:
        return f"<WekanList (id: {self.id}, title: {self.title})>"

    def __get_all_cards_on_list(self) -> list:
        """
        Get all cards by calling the API according to https://wekan.github.io/api/v7.42/#get_list
        :return: All cards
        """
        return self.board.client.fetch_json(f"/api/boards/{self.board.id}/lists/{self.id}/cards")

    def get_cards(self, regex_filter=".*") -> list[WekanCard]:
        """
        Get all (matching) cards
        :param regex_filter: Regex filter that will be applied to the search.
        :return: list of cards
        """
        all_cards = WekanCard.from_list(parent_list=self, data=self.__get_all_cards_on_list())
        return [card for card in all_cards if re.search(regex_filter, card.title)]

    def get_card_by_id(self, card_id: str) -> WekanCard:
        """
        Get a single Card by id
        :param card_id: id of the card to fetch data from
        :return: Instance of type WekanCard
        """
        response = self.board.client.fetch_json(
            f"/api/boards/{self.board.id}/lists/{self.id}/cards/{card_id}"
        )
        return WekanCard.from_dict(parent_list=self, data=response)

    @classmethod
    def from_dict(cls, parent_board: Board, data: dict) -> WekanList:
        """
        Creates an instance of class WekanList by using the API-Response of List creation.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of List creation.
        :return: Instance of class WekanList
        """
        return cls(parent_board=parent_board, list_id=data["_id"])

    @classmethod
    def from_list(cls, parent_board: Board, data: list) -> list[WekanList]:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of List creation.
        :return: Instances of class WekanList
        """
        instances = []
        for wekan_list in data:
            instances.append(cls(parent_board=parent_board, list_id=wekan_list["_id"]))
        return instances

    def update(self, title: str = None, position: int = None) -> WekanList:
        """Update list properties."""
        payload = {}
        if title is not None:
            payload["title"] = title
        if position is not None:
            payload["sort"] = position

        if payload:
            self.board.client.fetch_json(
                f"/api/boards/{self.board.id}/lists/{self.id}",
                http_method="PUT",
                payload=payload,
            )
            # Refresh data
            self.__init__(self.board, self.id)
        return self

    def archive(self) -> None:
        """Archive this list."""
        self.board.client.fetch_json(
            f"/api/boards/{self.board.id}/lists/{self.id}/archive", http_method="POST"
        )
        self.archived = True

    def restore(self) -> None:
        """Restore this list from archive."""
        self.board.client.fetch_json(
            f"/api/boards/{self.board.id}/lists/{self.id}/unarchive", http_method="POST"
        )
        self.archived = False

    def delete(self) -> None:
        """
        Delete the List instance.
        :return: None
        """
        self.board.client.fetch_json(
            f"/api/boards/{self.board.id}/lists/{self.id}", http_method="DELETE"
        )

    def create_card(self, title: str, description: str = "", members=None) -> WekanCard:
        """
        Creates a new card instance.
        :param title: Title of the new card.
        :param description: Description of the new card.
        :param members: Members of the new card.
        :return: Instance of type WekanCard
        """
        if members is None:
            members = []
        payload = {
            "title": title,
            "authorId": self.board.client.user_id,
            "members": members,
            "description": description,
            "swimlaneId": f"{self.board.id}",
        }
        response = self.board.client.fetch_json(
            uri_path=f"/api/boards/{self.board.id}/lists/{self.id}/cards",
            http_method="POST",
            payload=payload,
        )
        return WekanCard.from_dict(parent_list=self, data=response)
