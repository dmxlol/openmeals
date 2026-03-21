import os
import typing as t

from dotenv import load_dotenv

from libs.app import AppRegistry

ENVIRONMENT: t.Final[str] = os.getenv("ENVIRONMENT", "lde")

load_dotenv(".env")
load_dotenv(f".env.{ENVIRONMENT}")

from .config import settings  # noqa: E402

Apps = AppRegistry()
Apps.register_modules(settings)
