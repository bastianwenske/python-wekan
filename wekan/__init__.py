from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from wekan.board import Board
from wekan.card import WekanCard
from wekan.card_checklist import CardChecklist
from wekan.card_checklist_item import CardChecklistItem
from wekan.card_comment import CardComment
from wekan.customfield import Customfield
from wekan.integration import Integration
from wekan.label import Label
from wekan.swimlane import Swimlane
from wekan.user import WekanUser
from wekan.wekan_client import (
    UsernameAlreadyExists,
    WekanAPIError,
    WekanAuthenticationError,
    WekanClient,
    WekanConnectionError,
    WekanNotFoundError,
)
from wekan.wekan_list import WekanList

try:
    __version__ = _version("python-wekan")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "Board",
    "CardChecklist",
    "CardChecklistItem",
    "CardComment",
    "Customfield",
    "Integration",
    "Label",
    "Swimlane",
    "UsernameAlreadyExists",
    "WekanAPIError",
    "WekanAuthenticationError",
    "WekanCard",
    "WekanClient",
    "WekanConnectionError",
    "WekanList",
    "WekanUser",
]
