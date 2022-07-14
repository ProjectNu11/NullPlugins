from graia.saya import Channel

from library import config
from .base import BaseTrans
from .google import GoogleTrans
from .tencent import TencentTrans
from .youdao import YoudaoTrans

channel = Channel.current()

__all__: dict[BaseTrans, list[str]] = {
    "google": (GoogleTrans, GoogleTrans.get_languages()),
    "tencent": (TencentTrans, TencentTrans.get_languages()),
    "youdao": (YoudaoTrans, YoudaoTrans.get_languages()),
}


async def translate(
    content: str,
    source: str = None,
    target: str = None,
    keep: str = None,
    engine: str = None,
) -> str:
    """
    Translate content from source to target.

    :param content: content to translate
    :param source: source language
    :param target: target language
    :param keep: word to keep from translation
    :param engine: engine to use
    :return: translated content
    """

    if engine is None:
        engine = config.get_module_config(channel.module).get("default_engine")
    if not (engine := __all__.get(engine, None)):
        return (
            f"Invalid engine: {engine}.\n"
            f"Supported engines: {', '.join(__all__.keys())}"
        )
    trans_engine: BaseTrans = engine[0]
    languages: list[str] = engine[1]
    if source not in languages:
        return (
            f"Invalid source language: {source}.\n"
            f"Supported languages: {', '.join(languages)}"
        )
    if target not in languages:
        return (
            f"Invalid target language: {target}.\n"
            f"Supported languages: {', '.join(languages)}"
        )
    return await trans_engine.trans(content, source, target, keep)
