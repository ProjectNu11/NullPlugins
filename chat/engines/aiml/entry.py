from pathlib import Path

from module.translator.engines import BaseTrans
from .kernel import Kernel
from .lang_support import is_include_chinese


class AIML:
    translator: BaseTrans
    client: Kernel

    def __init__(self, trans: BaseTrans, **bot_predicate: str):
        self.translator = trans
        self.client = Kernel()
        for k, v in bot_predicate.items():
            self.client.set_bot_predicate(k, v)

    def load_aiml(self, files_dir: str, brain_path: str | None = None):
        if brain_path and Path(brain_path).exists():
            self.client.bootstrap(brain_file=brain_path)
        else:
            self.client.bootstrap(
                learn_files="startup.xml", commands="LOAD ALICE", chdir=files_dir
            )
            self.client.save_brain(brain_path)

    async def chat(
        self, message: str, session_id: int | None = None, translate: bool = True
    ):
        print(translate)
        if is_include_chinese(message):
            message = await self.translator.trans(message, trans_to="en")
        resp = self.client.respond(message, session_id)
        if not translate:
            return resp
        return await self.translator.trans(resp)
