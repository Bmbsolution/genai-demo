"""Scorecard plugins.

Importing this package makes the plugin contract available and registers every
concrete scorecard. As scorecards are implemented, import their modules here so
their ``__init_subclass__`` registration runs (e.g. ``from servicecat.scorecards
import documentation`` once F-07 lands).
"""

from servicecat.scorecards.base import (
    SCORECARD_REGISTRY,
    BaseScorecard,
    Evidence,
    Finding,
    Severity,
    get_scorecard,
)
from servicecat.scorecards.documentation import DocumentationScorecard

__all__ = [
    "SCORECARD_REGISTRY",
    "BaseScorecard",
    "DocumentationScorecard",
    "Evidence",
    "Finding",
    "Severity",
    "get_scorecard",
]
