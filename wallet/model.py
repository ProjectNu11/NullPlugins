from abc import abstractmethod
from enum import Enum


class Currency(Enum):
    value: float
    """ Value of the currency. """

    name: str
    """ Currency name """

    @classmethod
    @abstractmethod
    async def add(cls, field: int, supplicant: int, amount: int):
        pass

    @classmethod
    @abstractmethod
    async def charge(cls, field: int, supplicant: int, amount: int):
        pass

    @staticmethod
    @abstractmethod
    async def query(field: int, supplicant: int) -> int:
        pass

    @classmethod
    async def exchange(
        cls,
        field: int,
        supplicant: int,
        amount: int,
        currency: "Currency",
        on_failure: str = "余额不足",
    ) -> tuple[int, int]:
        """
        Exchange currency to other currency

        :param field: Group id
        :param supplicant: Supplicant id
        :param amount: Amount of currency
        :param currency: Currency to exchange to
        :param on_failure: Assertion message when insufficient balance
        :return: Amount of currency after exchange
        :exception: AssertionError
        """

        assert await cls.query(field, supplicant) >= amount, on_failure
        await cls.add(field, supplicant, amount)
        await currency.charge(field, supplicant, amount)
        return await cls.query(field, supplicant), await currency.query(
            field, supplicant
        )


class CurrencyExchange:
    registered_currency: list[Currency] = []
    """ Registered currency """

    @classmethod
    async def register(cls, currency: Currency):
        """
        Register currency to exchange

        :param currency: Currency to register
        :return: None
        :exception: AssertionError
        """

        cls.registered_currency.append(currency)
