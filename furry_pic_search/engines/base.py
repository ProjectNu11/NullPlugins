from abc import ABC, abstractmethod


class BaseSearch(ABC):
    __name__: str

    @abstractmethod
    async def get(self, *tags: str, **__) -> bytes:
        """
        Get a picture from the search engine.

        :param tags: The tags of the image.
        :return: The image data.
        """

        pass
