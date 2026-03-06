from abc import ABC, abstractmethod


class AuthenticationStrategy(ABC):
    @abstractmethod
    async def authenticate(self):
        pass
