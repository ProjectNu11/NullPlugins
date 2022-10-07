from abc import ABC, abstractmethod

from graia.ariadne.message.element import MusicShare


class BaseSearch(ABC):
    engine_name: str

    @staticmethod
    @abstractmethod
    async def search(*keywords: str) -> tuple[bytes, list[MusicShare]]:
        """
        Generate a picture from the search engine.

        :param keywords: The keywords to search.
        :return: The image data and the music share.
        """

        pass
