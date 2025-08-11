"""Python client library for WeKan REST API."""

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
from wekan.wekan_client import WekanClient
from wekan.wekan_list import WekanList

__all__ = [
    "Board",
    "WekanCard",
    "CardChecklist",
    "CardChecklistItem",
    "CardComment",
    "Customfield",
    "Integration",
    "Label",
    "Swimlane",
    "WekanUser",
    "WekanClient",
    "WekanList",
]

__version__ = "0.3.1"
