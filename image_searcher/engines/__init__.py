from .saucenao import saucenao_search, custom_cfg as saucenao_custom_cfg
from .ascii2d import ascii2d_search, custom_cfg as ascii2d_custom_cfg
from .ehentai import ehentai_search, custom_cfg as ehentai_custom_cfg
from .google import google_search, custom_cfg as google_custom_cfg
from .baidu import baidu_search, custom_cfg as baidu_custom_cfg

__engines__ = {
    "saucenao": saucenao_search,
    "ascii2d": ascii2d_search,
    "ehentai": ehentai_search,
    "google": google_search,
    "baidu": baidu_search,
}

custom_cfg_keys = {
    "saucenao": saucenao_custom_cfg,
    "ascii2d": ascii2d_custom_cfg,
    "ehentai": ehentai_custom_cfg,
    "google": google_custom_cfg,
    "baidu": baidu_custom_cfg,
}
