from abc import ABC, abstractmethod


class BaseTrans(ABC):
    @abstractmethod
    async def trans(self, content: str, *args) -> str:
        pass

    @abstractmethod
    def get_languages(self) -> list:
        pass
