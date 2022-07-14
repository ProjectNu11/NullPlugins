import random
import time
from hashlib import md5

from aiohttp import ClientSession

from library import config
from .base import BaseTrans


class YoudaoTrans(BaseTrans):
    __languages = [
        "AUTO",
        "ar",
        "de",
        "en",
        "es",
        "fr",
        "id",
        "it",
        "ja",
        "ko",
        "nl",
        "pt",
        "ru",
        "th",
        "vi",
        "zh-CHS",
    ]

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("This class is not meant to be instantiated")

    @classmethod
    async def trans(
        cls, content: str, trans_from: str = None, trans_to: str = None, *_
    ):
        if trans_from is None:
            trans_from = "AUTO"
        if trans_to is None:
            trans_to = "AUTO"
        assert trans_from in cls.__languages, f"{trans_from} not supported"
        assert trans_to in cls.__languages, f"{trans_to} not supported"
        salt, sign = cls.__get_salt(content)
        url = "http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule"
        headers = {
            "Cookie": "OUTFOX_SEARCH_USER_ID=-1927650476@223.97.13.65;",
            "Host": "fanyi.youdao.com",
            "Origin": "http://fanyi.youdao.com",
            "Referer": "http://fanyi.youdao.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/88.0.4324.146 Safari/537.36",
        }
        data = {
            "i": content,
            "from": trans_from,
            "to": trans_to,
            "smartresult": "dict",
            "client": "fanyideskweb",
            "salt": salt,
            "sign": sign,
            "version": "2.1",
            "keyfrom": "fanyi.web",
            "action": "FY_BY_REALTlME",
        }

        async with ClientSession(headers=headers) as session:
            async with session.post(url, data=data, proxy=config.proxy) as resp:
                result = await resp.json()
                print(result)
                return "".join(i["tgt"] for i in result["translateResult"][0])

    @classmethod
    def get_languages(cls) -> list[str]:
        return cls.__languages

    @staticmethod
    def __get_salt(content) -> tuple[str, str]:
        ts = str(round(time.time() * 1000))
        salt = ts + str(random.randint(0, 9))
        data = f"fanyideskweb{content}{salt}Tbh5E8=q6U3EXe+&L[4c@"
        sign = md5(data.encode("utf-8")).hexdigest()
        return salt, sign
