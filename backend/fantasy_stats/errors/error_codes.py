from enum import Enum


class JsonErrorCodes(Enum):
    TOO_SOON = "too_soon"
    LEAGUE_SIGNUP_FAILURE = "invalid_league"
    UNKNOWN_ERROR = "unknown_error"


class InvalidLeagueError(Exception):
    """Raised when a league is not found, inactive, or otherwise invalid."""

    pass
