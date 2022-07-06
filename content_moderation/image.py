import asyncio
import base64
import json
from datetime import datetime
from enum import Enum
from typing import NoReturn

from graia.saya import Channel
from sqlalchemy import select
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ims.v20201229 import ims_client, models

from library.config import config
from library.orm import orm
from .table import ImageModeration
from .util import tencent_credential

channel = Channel.current()


class ModerationLevel(Enum):
    Pass = "Pass"
    Review = "Review"
    Block = "Block"

    def __lt__(self, other: "ModerationLevel"):
        lv_map = {
            ModerationLevel.Pass: 1,
            ModerationLevel.Review: 2,
            ModerationLevel.Block: 3,
        }
        return lv_map[self] < lv_map[other]


def get_moderation_result(data_id: str, file_content: str) -> dict:
    try:
        return get_result(data_id, file_content)
    except TencentCloudSDKException as err:
        if str(err.code).startswith("AuthFailure"):
            tencent_credential.invalidate()
            raise
        tencent_credential.error_count_plus_one()
        raise


def get_result(data_id, file_content):
    cred = tencent_credential.get_credential()
    http_profile = HttpProfile()
    http_profile.endpoint = "ims.tencentcloudapi.com"
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client = ims_client.ImsClient(
        cred, config.get_module_config(channel.module, "server"), client_profile
    )
    req = models.ImageModerationRequest()
    params = {"DataId": data_id, "FileContent": file_content}
    req.from_json_string(json.dumps(params))
    resp = client.ImageModeration(req)
    return json.loads(resp.to_json_string())


async def async_get_moderation_result(data_id: str, file_content: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, get_moderation_result, data_id, file_content
    )


async def update(data_id: str, label: str, suggestion: str, sub_label: str) -> NoReturn:
    await orm.insert_or_update(
        ImageModeration,
        [ImageModeration.id == data_id],
        {
            "id": data_id,
            "time": datetime.now(),
            "label": label,
            "suggestion": suggestion,
            "sub_label": sub_label,
            "override": -1,
        },
    )


async def query(data_id: str) -> tuple[int, ModerationLevel, str] | None:
    if fetch := await orm.fetchone(
        select(
            ImageModeration.override,
            ImageModeration.suggestion,
            ImageModeration.sub_label,
        ).where(
            ImageModeration.id == data_id,
        )
    ):
        override, suggestion, sub_label = fetch
        return override, getattr(ModerationLevel, str(suggestion)), sub_label


async def run_image_moderation(image_id: str, data: bytes) -> tuple[bool, str]:
    if pre_check := await query(image_id):
        if pre_check[0] != -1:
            return bool(pre_check), pre_check[2]
        return pre_check[1] < ModerationLevel.Block, pre_check[2]
    if not tencent_credential.is_valid():
        return True, ""
    content = base64.b64encode(data).decode("utf-8")
    result = await async_get_moderation_result(image_id, content)
    await update(image_id, result["Label"], result["Suggestion"], result["SubLabel"])
    return (
        getattr(ModerationLevel, result["Suggestion"]) < ModerationLevel.Block,
        result["SubLabel"],
    )
