from abc import ABC, abstractmethod

from playwright.async_api import BrowserContext


class Module(ABC):
    def __init__(self, context: BrowserContext):
        self._context = context

    @abstractmethod
    def run(self):
        pass
