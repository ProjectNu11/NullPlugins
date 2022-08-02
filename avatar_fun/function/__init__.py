import inspect

from PIL.Image import Image

from .always import always
from .back_to_work import back_to_work
from .beat import beat
from .kiss import kiss
from .knife import knife
from .pat import pat
from .perfect import perfect
from .rip import rip
from .support import support
from .swallow import swallow
from .trash import trash
from .tuotoi import tuotoi

__all__ = {
    "一直": always,
    "继续打工": back_to_work,
    "打": beat,
    "亲": kiss,
    "刀": knife,
    "摸": pat,
    "完美": perfect,
    "撕": rip,
    "精神支柱": support,
    "吞": swallow,
    "垃圾探头": trash,
    "贴": tuotoi,
}


def check_and_run(name: str, *data: Image | str) -> bytes:
    annotation = inspect.signature(__all__[name]).parameters["data"].annotation
    arguments = [d for d in data if isinstance(d, annotation)]
    return __all__[name](*arguments)
