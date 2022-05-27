from __future__ import annotations

from wekan.base import WekanBase


class Integration(WekanBase):
    def __init__(self, parent_board, integration_id: str) -> None:
        """ Reference to a Wekan Integration """
        super().__init__()
        self.board = parent_board
        self.id = integration_id
        data = self.board.client.fetch_json(f'/api/boards/{self.board.id}/integrations/{self.id}')
        self.title = data.get('title', '')
        self.url = data['url']
        self.enabled = data['enabled']
        self.user_id = data['userId']
        self.activities = data['activities']
        self.created_at = self.board.client.parse_iso_date(data['createdAt'])
        self.modified_at = self.board.client.parse_iso_date(data['modifiedAt'])

    def __repr__(self) -> str:
        return f"<Integration (id: {self.id}, title: {self.title})>"

    @classmethod
    def from_dict(cls, parent_board, data: dict) -> Integration:
        """
        Creates an instance of class Integration by using the API-Response of Integration creation.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of Integration creation.
        :return: Instance of class Integration
        """
        return cls(parent_board=parent_board, integration_id=data['_id'])

    @classmethod
    def from_list(cls, parent_board, data: list) -> list:
        """
        Wrapper around function from_dict to process multiple objects within one function call.
        :param parent_board: Instance of Class Board pointing to the current Board
        :param data: Response of Integration creation.
        :return: Instances of class Integration
        """
        instances = []
        for integration in data:
            instances.append(cls(parent_board=parent_board, integration_id=integration['_id']))
        return instances

    def delete(self) -> None:
        """
        Delete the Integration instance according to https://wekan.github.io/api/v6.22/#delete_integration
        :return: None
        """
        self.board.client.fetch_json(f'/api/boards/{self.board.id}/integrations/{self.id}', http_method="DELETE")

    def delete_activities(self, activities: list) -> None:
        """
        Delete all subscribed activities according to https://wekan.github.io/api/v6.22/#delete_integration_activities
        :return: None
        """
        payload = {
            "activities": activities
        }
        self.board.client.fetch_json(f'/api/boards/{self.board.id}/integrations/{self.id}/activities',
                                     payload=payload,
                                     http_method="DELETE")

    def edit(self, enabled=None, title=None, url=None, token=None, activities=None) -> None:
        """
        Edit the current instance by sending a PUT Request to the API
        according to https://wekan.github.io/api/v6.22/#edit_integration
        :param enabled: is the integration enabled?
        :param title: new name of the integration
        :param url: new URL of the integration
        :param token: new token of the integration
        :param activities: new list of activities of the integration
        :return: None
        """
        payload = {}
        if enabled:
            payload["enabled"] = enabled
        if title:
            payload["title"] = title
        if url:
            payload["url"] = url
        if token:
            payload["token"] = token
        if activities:
            payload["activities"] = activities

        self.board.client.fetch_json(f'/api/boards/{self.board.id}/integrations/{self.id}',
                                     payload=payload, http_method="PUT")

    def change_title(self, new_title) -> None:
        """
        Set a new title for this instance.
        :param new_title: The new title.
        :return: None
        """
        self.edit(title=new_title)

    def enable(self) -> None:
        """
        Enable this integration.
        :return: None
        """
        self.edit(enabled=True)

    def add_activities(self, activities: list) -> None:
        """
        Add subscribed activities by sending a POST Request to the API
        according to https://wekan.github.io/api/v6.22/#new_integration_activities
        :param activities: the activities value
        :return: None
        """
        assert isinstance(activities, list)
        payload = {"activities": activities}
        self.board.client.fetch_json(f'/api/boards/{self.board.id}/integrations/{self.id}/activities',
                                     payload=payload, http_method="POST")
