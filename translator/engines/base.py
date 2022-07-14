from abc import ABC, abstractmethod


class BaseTrans(ABC):
    @abstractmethod
    async def trans(
        self,
        content: str,
        *args,
        trans_from: str | None = None,
        trans_to: str | None = None,
        **kwargs
    ) -> str:
        pass

    @abstractmethod
    def get_languages(self) -> list:
        pass
