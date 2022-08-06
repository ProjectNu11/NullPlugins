import asyncio
import json
import pickle
from pathlib import Path

from graia.saya import Channel
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tmt.v20180321 import tmt_client, models

from library import config
from .base import BaseTrans

channel = Channel.current()


class TencentCredential:
    __cred: credential.Credential = None
    __shared: Path = Path(config.path.shared, "tencent_credential.pickle")
    __valid: bool

    def __init__(self, module: str):
        if cred := self.__load_shared_credential_pickle():
            self.__cred = cred
            self.__valid = True
            return
        cfg = config.get_module_config(module)
        if not cfg:
            self.__valid = False
            return
        if not cfg.get("secret_id", None) or not cfg.get("secret_key", None):
            self.__valid = False
            return
        else:
            self.__cred = credential.Credential(
                cfg["tencent_secret_id"], cfg["tencent_secret_key"]
            )
            self.__save_shared_credential_pickle()
            self.__valid = True

    def invalidate(self):
        self.__valid = False

    def is_valid(self):
        return self.__valid

    def get_credential(self):
        return self.__cred

    def __load_shared_credential_pickle(self):
        if not self.__shared.exists():
            return
        with self.__shared.open("rb") as f:
            return pickle.load(f)

    def __save_shared_credential_pickle(self):
        with self.__shared.open("wb") as f:
            pickle.dump(self.__cred, f)


tencent_credential = TencentCredential(channel.module)


class TencentTrans(BaseTrans):
    __languages_source = [
        "auto",
        "zh",
        "zh-TW",
        "en",
        "ja",
        "ko",
        "fr",
        "es",
        "it",
        "de",
        "tr",
        "ru",
        "pt",
        "vi",
        "id",
        "th",
        "ms",
        "ar",
        "hi",
    ]
    __languages_target = [
        "ms",
        "pt",
        "id",
        "it",
        "zh",
        "ru",
        "tr",
        "ar",
        "fr",
        "th",
        "es",
        "de",
        "zh-TW",
        "hi",
        "en",
        "ko",
        "vi",
        "ja",
    ]

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("This class is not intended to be instantiated.")

    @classmethod
    def sync_trans(
        cls,
        content: str,
        trans_from: str = None,
        trans_to: str = None,
        keep: str = None,
        *_,
    ) -> str | None:
        if trans_from is None:
            trans_from = "auto"
        if trans_to is None:
            trans_to = "zh"
        if keep is None:
            keep = ""
        try:
            assert trans_from in cls.__languages_source, f"{trans_from} not supported"
            assert trans_to in cls.__languages_target, f"{trans_to} not supported"
            assert (cred := tencent_credential.get_credential()), "Invalid credential"
            http_profile = HttpProfile()
            http_profile.endpoint = "tmt.tencentcloudapi.com"
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client = tmt_client.TmtClient(cred, "ap-guangzhou", client_profile)
            req = models.TextTranslateRequest()
            params = {
                "SourceText": content,
                "Source": trans_from,
                "Target": trans_to,
                "ProjectId": 0,
                "UntranslatedText": keep,
            }
            req.from_json_string(json.dumps(params))
            resp = client.TextTranslate(req)
            response: dict = json.loads(resp.to_json_string())
            return response["TargetText"]
        except TencentCloudSDKException as err:
            return err.message
        except AssertionError as err:
            return err.args[0]

    @classmethod
    async def trans(
        cls,
        content: str,
        trans_from: str = "auto",
        trans_to: str = "zh",
        keep: str = "",
        *_,
    ) -> str | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, cls.sync_trans, content, trans_from, trans_to, keep
        )

    @classmethod
    def get_languages(cls) -> list[str]:
        return list(set(cls.__languages_source + cls.__languages_target))
