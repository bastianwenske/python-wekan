from __future__ import annotations

from wekan.base import WekanBase


class Customfield(WekanBase):
    def __init__(self, parent_board, custom_field_id: str) -> None:
        """ Reference to a Customfield within a Wekan Board """
        super().__init__()
        self.board = parent_board
        self.id = custom_field_id

        data = self.board.client.fetch_json(f'/api/boards/{self.board.id}/custom-fields/{self.id}')
        self.name = data['name']
        self.type = data['type']
        self.board_ids = data['boardIds']
        self.type = data['type']
        self.settings = data['settings']
        self.show_on_card = data['showOnCard']
        self.automatically_on_card = data['automaticallyOnCard']
        self.show_label_on_mini_card = data['showLabelOnMiniCard']

    def __repr__(self) -> str:
        return f"<Customfield (name: {self.name}, id: {self.id})>"

    @classmethod
    def from_dict(cls, parent_board, data: dict) -> Customfield:
        """
        Creates an instance of class Customfield by using the API-Response of Customfield GET.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of CustomField creation.
        :return: Instance of class CustomField
        """
        return cls(parent_board=parent_board, custom_field_id=data['_id'])

    @classmethod
    def from_list(cls, parent_board, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of CustomField creation.
        :return: Instances of class CustomField
        """
        instances = [cls(parent_board=parent_board, custom_field_id=field['_id']) for field in data]
        return instances

    def delete(self) -> dict:
        """
        Delete the CustomField instance according to https://wekan.github.io/api/v6.22/#get_custom_field
        :return: API Response as type dict containing the id of the deleted CustomField
        """
        return self.board.client.fetch_json(f'/api/boards/{self.board.id}/custom-fields/{self.id}',
                                            http_method="DELETE")

    def edit(self, data: dict) -> None:
        """
        Edit the current instance by sending a PUT Request to the API.
        :param data: Changed fields as dict object. Example: {'title': 'changed title'}
        :return: API Response as type dict containing the id of the changed CustomField
        """
        return self.board.client.fetch_json(f'/api/boards/{self.board.id}/custom-fields/{self.id}',
                                            payload=data, http_method="PUT")
