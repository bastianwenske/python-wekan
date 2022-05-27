from __future__ import annotations

from wekan.base import WekanBase


class CardComment(WekanBase):
    def __init__(self, parent_card, comment_id: str) -> None:
        """ Reference to a Wekan CardComment """
        super().__init__()
        self.card = parent_card
        self.id = comment_id

        uri = f'/api/boards/{self.card.list.board.id}/cards/{self.card.id}/comments/{self.id}'
        data = self.card.list.board.client.fetch_json(uri)
        self.text = data['text']
        self.author_id = data['userId']
        self.createdAt = self.card.list.board.client.parse_iso_date(data['createdAt'])
        self.modified_at = self.card.list.board.client.parse_iso_date(data['modifiedAt'])

    def __repr__(self) -> str:
        return f"<CardComment (id: {self.id}, text: {self.text})>"

    @classmethod
    def from_dict(cls, parent_card, data: dict) -> CardComment:
        """
        Creates an instance of class CardComment by using the API-Response of CardComment GET.
        :param parent_card: Instance of Class Card pointing to the Card of this Comment
        :param data: Response of CardComment GET.
        :return: Instance of class CardComment
        """
        return cls(parent_card=parent_card, comment_id=data['_id'])

    @classmethod
    def from_list(cls, parent_card, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_card: Instance of Class Card pointing to the current Card of this Comment
        :param data: Response of CardComment GET.
        :return: Instances of class CardComment
        """
        instances = []
        for comment in data:
            instances.append(cls(parent_card=parent_card, comment_id=comment['_id']))
        return instances

    def edit(self, data: dict) -> None:
        """
        Edit the current instance by sending a PUT Request to the API.
        Currently, this is not supported by API.
        See also: https://wekan.github.io/api/v6.22/#wekan-rest-api-cardcomments
        """
        raise NotImplementedError

    def delete(self) -> None:
        """
        Delete the CardComment instance according to https://wekan.github.io/api/v6.22/#delete_comment
        :return: None
        """
        uri = f'/api/boards/{self.card.list.board.id}/cards/{self.card.id}/comments/{self.id}'
        self.card.list.board.client.fetch_json(uri, http_method="DELETE")
