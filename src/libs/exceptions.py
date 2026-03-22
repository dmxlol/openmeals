from starlette import status


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"
    extra: list | dict

    def __init__(
        self, detail: str | None = None, status_code: int | None = None, extra: dict | list | None = None
    ) -> None:
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if extra is not None:
            self.extra = extra
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Not found"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Forbidden"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Unauthorized"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflict"


class TimeoutError(AppError):
    status_code = status.HTTP_408_REQUEST_TIMEOUT
    detail = "Request timeout"
