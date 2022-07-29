from pathlib import Path

from graia.saya.channel import Channel

from library.config import config

channel = Channel.current()

channel.name("ChitungPython")
channel.author(
    "角川烈&白门守望者 (Chitung-public), "
    "nullqwertyuiop (Chitung-python), "
    "IshikawaKaito (Chitung-python)"
)
channel.description("七筒")

Path(config.path.data, channel.module).mkdir(exist_ok=True)

from .auto_reply import *
from .bank import *
from .dice import *
from .event_listener import *
from .fishing import *
from .fortune_teller import *
from .help import *
from .lottery import *
from .lovely_image import *
from .ow_hero_lines import *
from .utils import *
