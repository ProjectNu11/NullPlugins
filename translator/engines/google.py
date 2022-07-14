import json
import urllib.parse

from aiohttp import ClientSession

from library import config
from .base import BaseTrans


class GoogleTrans(BaseTrans):
    __languages = [
        "af",
        "sq",
        "am",
        "ar",
        "hy",
        "as",
        "ay",
        "az",
        "bm",
        "eu",
        "be",
        "bn",
        "bho",
        "bs",
        "bg",
        "ca",
        "ceb",
        "ny",
        "zh-CN",
        "co",
        "hr",
        "cs",
        "da",
        "dv",
        "doi",
        "nl",
        "en",
        "eo",
        "et",
        "ee",
        "tl",
        "fi",
        "fr",
        "fy",
        "gl",
        "ka",
        "de",
        "el",
        "gn",
        "gu",
        "ht",
        "ha",
        "haw",
        "iw",
        "hi",
        "hmn",
        "hu",
        "is",
        "ig",
        "ilo",
        "id",
        "ga",
        "it",
        "ja",
        "jw",
        "kn",
        "kk",
        "km",
        "rw",
        "gom",
        "ko",
        "kri",
        "ku",
        "ckb",
        "ky",
        "lo",
        "la",
        "lv",
        "ln",
        "lt",
        "lg",
        "lb",
        "mk",
        "mai",
        "mg",
        "ms",
        "ml",
        "mt",
        "mi",
        "mr",
        "mni-Mtei",
        "lus",
        "mn",
        "my",
        "ne",
        "no",
        "or",
        "om",
        "ps",
        "fa",
        "pl",
        "pt",
        "pa",
        "qu",
        "ro",
        "ru",
        "sm",
        "sa",
        "gd",
        "nso",
        "sr",
        "st",
        "sn",
        "sd",
        "si",
        "sk",
        "sl",
        "so",
        "es",
        "su",
        "sw",
        "sv",
        "tg",
        "ta",
        "tt",
        "te",
        "th",
        "ti",
        "ts",
        "tr",
        "tk",
        "ak",
        "uk",
        "ur",
        "ug",
        "uz",
        "vi",
        "cy",
        "xh",
        "yi",
        "yo",
        "zu",
    ]

    @classmethod
    async def trans(
        cls, content: str, trans_from: str = None, trans_to: str = None, *_
    ):
        if trans_from is None:
            trans_from = "auto"
        if trans_to is None:
            trans_to = "zh-CN"
        assert (
            trans_from in cls.__languages or trans_from == "auto"
        ), f"{trans_from} not supported"
        assert trans_to in cls.__languages, f"{trans_to} not supported"
        url = (
            "http://clients5.google.com/translate_a/t?"
            f"client=dict-chrome-ex&"
            f"sl={trans_from}&tl={trans_to}"
            f"&q={urllib.parse.quote(content)}"
        )
        async with ClientSession() as session:
            async with session.get(url, proxy=config.proxy) as resp:
                result = json.loads(await resp.text())
                if trans_from == "auto":
                    return result[0][0]
                return result[0]

    @classmethod
    def get_languages(cls) -> list[str]:
        return cls.__languages
