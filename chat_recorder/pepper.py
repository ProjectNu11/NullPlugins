from graia.saya import Channel

from library.config import get_module_config, update_module_config

channel = Channel.current()

if not (pepper := get_module_config(channel.module, "pepper")) or len(pepper) != 16:
    pepper = "".join(
        __import__("random").SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(16)
        if (string := __import__("string"))
    )
    update_module_config(
        channel.module,
        {"pepper": pepper},
    )
