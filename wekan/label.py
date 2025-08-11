"""Label management for WeKan boards."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from wekan.board import Board

from wekan.base import WekanBase


class Label(WekanBase):
    """Represents a WeKan board label."""

    def __init__(self, parent_board: Board, label_id: str, name: str, color="") -> None:
        """Reference to a Wekan Label."""
        super().__init__()
        self.board = parent_board
        self.id = label_id
        self.name = name
        self.color = color

    def __repr__(self) -> str:
        """Return string representation of the Label."""
        return f"<Label (name: {self.name}, id: {self.id}, color={self.color})>"

    @classmethod
    def from_dict(cls, parent_board: Board, data: dict) -> Label:
        """Creates an instance of class Label by using the API-Response of Label GET.

        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of Label creation.
        :return: Instance of class Label
        """
        return cls(
            parent_board=parent_board,
            label_id=data["_id"],
            name=data["name"],
            color=data["color"],
        )

    @classmethod
    def from_list(cls, parent_board: Board, data: list) -> list[Label]:
        """Wrapper around function from_dict to process multiple objects within one function call.

        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of Label creation.
        :return: Instances of class Label
        """
        instances = []
        for label in data:
            instances.append(
                cls(
                    parent_board=parent_board,
                    label_id=label["_id"],
                    name=label["name"],
                    color=label["color"],
                )
            )
        return instances

    def delete(self) -> None:
        """Delete this Label instance.

        Currently, not supported by API: https://wekan.github.io/api/v7.42/#wekan-rest-api-boards
        """
        raise NotImplementedError

    def edit(self, data: dict) -> None:
        """Edit the current instance by sending a PUT Request to the API.

        Currently, not supported by API: https://wekan.github.io/api/v7.42/#wekan-rest-api-boards
        """
        raise NotImplementedError
