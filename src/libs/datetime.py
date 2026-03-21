from datetime import UTC, datetime


def utcnow():
    return datetime.now(tz=UTC)
