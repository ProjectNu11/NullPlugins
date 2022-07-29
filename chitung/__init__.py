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

channel = Channel.current()

channel.name("ChitungPython")
channel.author(
    "角川烈&白门守望者 (Chitung-public), "
    "nullqwertyuiop (Chitung-python), "
    "IshikawaKaito (Chitung-python)"
)
channel.description("七筒")
