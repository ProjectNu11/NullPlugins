from abc import ABC, abstractmethod

from PIL.Image import Image


class BaseSearch(ABC):
    __name__: str

    @abstractmethod
    async def get(self, *tags: str, **__) -> Image:
        """
        Get a picture from the search engine.

        :param tags: The tags of the image.
        :return: The image data.
        """

        pass
