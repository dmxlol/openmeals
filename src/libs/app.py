import contextlib
import inspect
import typing as t
from functools import lru_cache
from importlib import import_module as imp

from fastapi import APIRouter
from sqlmodel import SQLModel

if t.TYPE_CHECKING:
    from core.config import Settings


class AppRegistry:
    __instance = None
    __registry = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self.__registry = {}

    def register_modules(self, settings: "Settings"):
        for module in settings.modules:
            self.__registry[module] = imp(module)

    @lru_cache
    def get_all_models(self):
        modules = []
        for module in self.__registry.keys():
            with contextlib.suppress(ImportError):
                modules.append(imp(f"{module}.models"))

        return [
            member
            for module in modules
            for _, member in inspect.getmembers(module)
            if inspect.isclass(member) and issubclass(member, SQLModel) and member != SQLModel
        ]

    @lru_cache
    def get_all_routers(self) -> list[APIRouter]:
        routers = []
        for module in self.__registry.keys():
            with contextlib.suppress(ImportError):
                handlers = imp(f"{module}.handlers")
                for _, member in inspect.getmembers(handlers):
                    if isinstance(member, APIRouter):
                        routers.append(member)
        return routers
