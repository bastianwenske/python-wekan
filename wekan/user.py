from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from wekan.wekan_client import WekanClient

from wekan.base import WekanBase
from wekan.board import Board


class WekanUser(WekanBase):
    def __init__(self, client: WekanClient, user_id: str) -> None:
        """Reference to a Wekan User"""
        super().__init__()
        self.id = user_id
        self.client = client

        data = self.client.fetch_json(f"/api/users/{self.id}")
        self.username = data["username"]
        self.created_at = self.client.parse_iso_date(data["createdAt"])
        self.modified_at = self.client.parse_iso_date(data["modifiedAt"])
        self.services = data["services"]
        self.emails = data["emails"]
        self.profile = data["profile"]
        self.authentication_method = data["authenticationMethod"]
        self.session_data = data["sessionData"]
        self.import_usernames = data.get("importUsernames", [])
        self.orgs = data.get("orgs", [])
        self.teams = data.get("teams", [])
        self.boards = data.get("boards", [])
        self.is_admin = data.get("isAdmin", False)

    def __repr__(self) -> str:
        return f"<WekanUser (id: {self.id}, username: {self.username})>"

    def get_boards(self) -> list[Board]:
        """Get boards accessible to this user."""
        board_data = self.client.fetch_json(f"/api/users/{self.id}/boards")
        return [Board(client=self.client, board_id=b["_id"]) for b in board_data]

    @classmethod
    def from_dict(cls, client: WekanClient, data: dict) -> WekanUser:
        """
        Creates an instance of class WekanUser by using the API-Response of User GET.
        :param client: Instance of Class WekanClient pointing to the Client
        :param data: Response of User GET.
        :return: Instance of class WekanUser
        """
        return cls(client=client, user_id=data["_id"])

    @classmethod
    def from_list(cls, client: WekanClient, data: list) -> list[WekanUser]:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param client: Instance of Class WekanClient pointing to the Client
        :param data: Responses of User GET.
        :return: Instances of class WekanUser
        """
        instances = []
        for user in data:
            instances.append(cls(client=client, user_id=user["_id"]))
        return instances

    def delete(self) -> None:
        """
        Delete the User instance according to https://wekan.github.io/api/v7.42/delete_user
        :return: None
        """
        self.client.fetch_json(f"/api/users/{self.id}", http_method="DELETE")

    def edit(self, action: str) -> None:
        """
        Edit the current instance by sending a PUT Request to the API
        according to https://wekan.github.io/api/v7.42/#edit_user.
        :param action: Type of action. See also allowed_actions.
        :return: None
        """
        allowed_actions = ["takeOwnership", "disableLogin", "enableLogin"]
        assert action in allowed_actions, f"action not in {allowed_actions}"
        self.client.fetch_json(
            f"/api/user/{self.id}", payload={"action": action}, http_method="PUT"
        )
