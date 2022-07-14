from abc import ABC, abstractmethod


class BaseChat(ABC):
    @abstractmethod
    async def chat(
        self, message: str, sender: int, *_, translate: bool = True, **__
    ) -> str:
        pass
