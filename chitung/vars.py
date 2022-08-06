from pathlib import Path

from graia.ariadne.message.parser.twilight import FullMatch, SpacePolicy, UnionMatch

from library import PrefixMatch, config

ASSETS = Path(Path(__file__).parent, "assets")
CHITUNG_PREFIX = [PrefixMatch, FullMatch("qt").space(SpacePolicy.FORCE)]
OK_CHITUNG_PREFIX = UnionMatch(
    "ok", "OK", "OK", *[f"{prefix}qt" for prefix in config.func.prefix]
).space(SpacePolicy.FORCE)
