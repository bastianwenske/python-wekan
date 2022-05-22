import json
from datetime import datetime, timezone
import requests
from dateutil import parser
from wekan.board import Board
from wekan.user import User


class WekanClient(object):
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self.__renew_login_data()
        self.users = User.from_list(client=self, data=self.get_all_users())
        self.boards = Board.from_list(self, data=self.get_boards())
        self.public_boards = Board.from_list(self, data=self.get_public_boards())

    def __renew_login_data(self):
        """
        Set the variables we need for login. Generating the token before.
        """
        self.user_id, self.token, self.token_expire_date = self.__get_api_token()

    def __get_api_token(self):
        """
        Get the API token by calling the login endpoint.
        Return: user_id, token, tokenExpires
        """
        credentials = {
            "username": self.username,
            "password": self.password
        }
        json_obj = self.fetch_json('/users/login',
                                   http_method='POST',
                                   payload=credentials)
        return json_obj['id'], json_obj['token'], json_obj['tokenExpires']

    def get_all_users(self) -> list:
        """
        Get all users by calling the API according to https://wekan.github.io/api/v2.55/#get_all_users
        IMPORTANT: Only the admin user (the first user) can call this REST API Endpoint.
        :return: List of instances of class User
        """
        return self.fetch_json(f'/api/users')

    @staticmethod
    def parse_iso_date(date: datetime.date) -> datetime.date:
        """
        Read in a datetime.date object for converting it to ISO format.
        :param date: date object in non iso format
        :return: date in parsed iso format
        """
        return parser.isoparse(date)

    def __is_api_token_expired(self) -> bool:
        """
        Returns whether api token is expired or not.
        :return: status
        :rtype: bool
        """
        now = datetime.now().replace(tzinfo=timezone.utc)
        expire_date = self.parse_iso_date(self.token_expire_date)
        return expire_date < now

    def fetch_json(self, uri_path, http_method="GET", payload=None):
        """
        Make a request to the wekan api.
        :return: Response body
        :rtype: dict (json)
        """
        url = self.base_url + uri_path
        headers = {'Content-Type': 'application/json; charset=utf-8'}

        if payload is None:
            payload = {}

        try:
            if self.token_expire_date and self.__is_api_token_expired():
                self.__renew_login_data()
            headers['Authorization'] = f'Bearer {self.token}'
        except AttributeError:
            # pass if the variable self.token_expire_date isn't defined
            pass

        try:
            response = requests.request(method=http_method,
                                        url=url, headers=headers,
                                        data=json.dumps(payload))
            if response.status_code not in (200, 201) or 'error' in response.json():
                raise Exception(f'Error while talking to API. Please see HTTP-Response: \n {response.text}')
        except requests.exceptions.JSONDecodeError:
            raise Exception('Could not decode the API response.')

        return response.json()

    def get_public_boards(self) -> dict:
        """
        Returns all public boards.

        :return: a list of Python objects representing the Wekan boards.
        :rtype: list of Board

        Each board has the following noteworthy attributes:
            TODO
        """
        return self.fetch_json(uri_path=f'/api/boards')

    def get_boards(self) -> dict:
        """
        Returns all boards for your Wekan user.
        :return: a list of Python objects representing the Wekan boards.
        :rtype: list of Board
        """
        return self.fetch_json(uri_path=f'/api/users/{self.user_id}/boards')

    def get_board_by_title(self, title) -> Board:
        """
        Get board by title.
        :return: Instance of Swimlane
        """
        for board in self.boards:
            if title == board.title:
                return board

    def add_board(self, title: str, color: str, owner=None,
                  is_admin=True, is_active=True, is_no_comments=False,
                  is_comment_only=False, permission='private') -> Board:
        """
        Creates a new board according to https://wekan.github.io/api/v2.55/#new_board
        :param title: Title of the board.
        :param color: Color of the board.
        :param owner: Owner (ID) of the board.
        :param is_admin: Bool defines if the board creator is admin.
        :param is_active: Bool defines if the board is active.
        :param is_no_comments: Bool defines if comments are allowed.
        :param is_comment_only: Bool defines if only comments are allowed.
        :param permission: Permissions of the board.
        :return: Board creation response
        :rtype: list
        """
        payload = {
            'title': title,
            'owner': self.user_id if not owner else owner,
            'isAdmin': is_admin,
            'isActive': is_active,
            'isNoComments': is_no_comments,
            'isCommentOnly': is_comment_only,
            'permission': permission,
            'color': color
        }
        response = self.fetch_json(uri_path='/api/boards', http_method="POST", payload=payload)
        instance = Board.from_dict(client=self, data=response)
        self.boards.append(instance)
        return instance

    def add_user(self, username: str, email: str, password: str) -> User:
        """
        Creates a new board according to https://wekan.github.io/api/v2.55/#new_user
        :param username: Username of the new user.
        :param email: E-Mail of the new user.
        :param password: Passwort of the new user.
        :return: Instance of class User
        """
        payload = {
            'username': username,
            'email': email,
            'password': password
        }
        response = self.fetch_json(uri_path='/api/users', http_method="POST", payload=payload)
        instance = User.from_dict(client=self, data=response)
        self.users.append(instance)
        return instance
