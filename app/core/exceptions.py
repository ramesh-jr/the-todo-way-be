"""Custom exception classes for consistent error handling."""

from fastapi import HTTPException


class AppException(HTTPException):
    """Base application exception that maps to an API error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(404, f"{resource} not found")


class ConflictException(AppException):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, detail: str) -> None:
        super().__init__(409, detail)
