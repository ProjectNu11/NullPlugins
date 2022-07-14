"""
MIT License

Copyright (c) 2017 Yalei Meng

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from pathlib import Path

from graia.saya import Channel

from library import config
from module.translator.engines import get_engine
from .entry import AIML
from ..base import BaseChat

channel = Channel.current()
data_dir = Path(config.path.data, channel.module)
data_dir.mkdir(exist_ok=True)

aiml = AIML(
    get_engine(),
    name=f" {config.name}",
    gender=" boy",
    mother=" Mother",
    father=" Father",
    phylum=" Robot",
    master=" Master",
    botmaster=" Master",
    birth=" 2020-06-04",
    birthplace=" Void",
    location=" Null",
    age=" 2",
    kingdom=" Kingdom",
    religion=" None",
    family=f" {config.name}'s",
    order=" Order",
)

aiml_files = str(Path(Path(__file__).parent, "alice"))
aiml_brain = str(Path(data_dir, "aiml_brain.brn"))
aiml.load_aiml(aiml_files, aiml_brain)


class AIMLChat(BaseChat):
    @staticmethod
    async def chat(message: str, sender: int, *_, translate: bool = True, **__) -> str:
        return await aiml.chat(message, sender, translate)
