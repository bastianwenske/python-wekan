import json
import re
from datetime import datetime, timezone

import requests

from wekan.board import Board
from wekan.user import WekanUser


class WekanAPIError(Exception):
    """Base exception for Wekan API errors."""

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code


class WekanNotFoundError(WekanAPIError):
    """Resource not found (404)."""


class WekanAuthenticationError(WekanAPIError):
    """Authentication failed (401)."""


class UsernameAlreadyExists(WekanAPIError):
    pass


class WekanClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url
        self.username = username
        self.password = password
        self.__renew_login_data()

    def __renew_login_data(self):
        """
        Set the variables we need for login. Generating the token before.
        """
        self.user_id, self.token, self.token_expire_date = self.__get_api_token()

    def __get_public_boards(self) -> dict:
        """
        Returns all public boards.
        :return: a list of Python objects representing the Wekan boards.
        """
        return self.fetch_json(uri_path="/api/boards")

    def __get_boards(self) -> dict:
        """
        Returns all boards for your Wekan user.
        :return: a list of Python objects representing the Wekan boards.
        """
        return self.fetch_json(uri_path=f"/api/users/{self.user_id}/boards")

    def list_boards(self, regex_filter=".*") -> list[Board]:
        """
        List all (matching) boards
        :return: list of boards
        """
        public_boards = Board.from_list(self, data=self.__get_public_boards())
        private_boards = Board.from_list(self, data=self.__get_boards())
        all_boards = public_boards + private_boards
        return [board for board in all_boards if re.search(regex_filter, board.title)]

    def __get_all_users(self) -> list:
        """
        Get all users by calling the API according to
        https://wekan.github.io/api/v7.42/#get_all_users
        IMPORTANT: Only the admin user (the first user) can call this REST API Endpoint.
        :return: List of instances of class WekanUser
        """
        return self.fetch_json("/api/users")

    def get_users(self, regex_filter=".*") -> list[WekanUser]:
        """
        Get all (matching) users
        :return: list of users
        """
        all_users = WekanUser.from_list(client=self, data=self.__get_all_users())
        return [user for user in all_users if re.search(regex_filter, user.username)]

    def get_current_user(self) -> WekanUser:
        """Get current user details."""
        return WekanUser(client=self, user_id=self.user_id)

    def find_user(self, username: str = None, email: str = None) -> WekanUser:
        """Find user by username or email."""
        if not username and not email:
            raise ValueError("Either username or email must be provided.")

        users = self.get_users()
        for user in users:
            if username and user.username == username:
                return user
            if email and email in [e["address"] for e in user.emails]:
                return user
        return None

    def __get_api_token(self):
        """
        Get the API token by calling the login endpoint.
        Return: user_id, token, tokenExpires
        """
        credentials = {"username": self.username, "password": self.password}
        json_obj = self.fetch_json("/users/login", http_method="POST", payload=credentials)
        return json_obj["id"], json_obj["token"], json_obj["tokenExpires"]

    @staticmethod
    def parse_iso_date(date_str: str) -> datetime:
        """
        Parse ISO 8601 date string to datetime object.
        :param date_str: Date string in ISO format
        :return: Parsed datetime object
        """
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return datetime.fromisoformat(date_str)

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
        headers = {"Content-Type": "application/json; charset=utf-8"}

        if payload is None:
            payload = {}

        try:
            if self.token_expire_date and self.__is_api_token_expired():
                self.__renew_login_data()
            headers["Authorization"] = f"Bearer {self.token}"
        except AttributeError:
            # pass if the variable self.token_expire_date isn't defined
            pass

        response = requests.request(
            method=http_method, url=url, headers=headers, data=json.dumps(payload)
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise WekanAuthenticationError(
                    f"Authentication failed: {e.response.text}", e.response.status_code
                )
            if e.response.status_code == 404:
                raise WekanNotFoundError(
                    f"Resource not found: {e.response.text}", e.response.status_code
                )

            # Special case for username exists
            try:
                if "Username already exists" in e.response.json().get("reason", ""):
                    raise UsernameAlreadyExists("Username already exists")
            except json.JSONDecodeError:
                pass  # Not a JSON response, fall through to generic error

            raise WekanAPIError(f"API error: {e.response.text}", status_code=e.response.status_code)

        try:
            return response.json()
        except json.JSONDecodeError:
            # Handle cases where API returns non-JSON success response (e.g. DELETE calls)
            if response.status_code in (200, 201, 204) and not response.text:
                return {}  # Return empty dict for success with no content

            if response.status_code == 500 and http_method == "DELETE":
                # There are errors when deleting some resources via api e.g.
                # delete cards responds with "Internal Server Error" and
                # status 500 even if the card has been deleted successfully
                return response.text  # Keep this legacy behavior for now

            raise WekanAPIError(
                f"Could not decode the API response. Please see HTTP-Response: \n {response.text}"
            )

    def add_board(
        self,
        title: str,
        color: str,
        owner=None,
        is_admin=True,
        is_active=True,
        is_no_comments=False,
        is_comment_only=False,
        permission="private",
    ) -> Board:
        """
        Creates a new board according to https://wekan.github.io/api/v7.42/#new_board
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
            "title": title,
            "owner": self.user_id if not owner else owner,
            "isAdmin": is_admin,
            "isActive": is_active,
            "isNoComments": is_no_comments,
            "isCommentOnly": is_comment_only,
            "permission": permission,
            "color": color,
        }
        response = self.fetch_json(uri_path="/api/boards", http_method="POST", payload=payload)
        return Board.from_dict(client=self, data=response)

    def add_user(self, username: str, email: str, password: str) -> WekanUser:
        """Creates a new user according to https://wekan.github.io/api/v7.42/#new_user.

        :param username: Username of the new user.
        :param email: E-Mail of the new user.
        :param password: Password of the new user.
        :return: Instance of class WekanUser
        """
        payload = {"username": username, "email": email, "password": password}
        response = self.fetch_json(uri_path="/api/users", http_method="POST", payload=payload)
        return WekanUser.from_dict(client=self, data=response)
