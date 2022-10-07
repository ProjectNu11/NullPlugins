import asyncio
import base64
import math
import re
from io import BytesIO

import numpy
from PIL import Image as PillowImage
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    WildcardMatch,
    RegexResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library import prefix_match
from library.depend import Switch, Blacklist, FunctionCall

channel = Channel.current()


@channel.use(
    ListenerSchema(
        [GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    prefix_match(),
                    FullMatch("图片编码"),
                    WildcardMatch().flags(re.S) @ "text",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def image_coder(app: Ariadne, event: MessageEvent, text: RegexResult):
    if not text.matched or not text.result.display:
        return
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            Image(data_bytes=await asyncio.to_thread(encode_image, text.result.display))
        ),
    )


def encode_image(original: str | bytes) -> bytes:
    if isinstance(original, str):
        original = original.encode("utf-8")
        is_str = True
    else:
        is_str = False

    processed_input = base64.b85encode(original).decode("utf-8")

    canvas_x = math.ceil(math.sqrt((len(processed_input) + 1) / 4))
    length = canvas_x * canvas_x

    data = numpy.zeros((canvas_x, canvas_x, 4), numpy.uint8)

    for index in range(length):
        if index == 0:
            data[0, 0] = [int(is_str), 0, 0, 0]
            continue
        row = index // canvas_x
        col = index % canvas_x
        if part := processed_input[(index - 1) * 4 : index * 4]:
            colors = [ord(char) for char in part]
            colors.extend([0 for _ in range((4 - len(colors)))])
            red, green, blue, alpha = colors
            data[row, col] = [red, green, blue, alpha]
            continue

    output = BytesIO()
    PillowImage.fromarray(data).save(output, "PNG")

    return output.getvalue()


def decode_image(image: PillowImage.Image | bytes) -> str | bytes:
    if isinstance(image, bytes):
        image = PillowImage.open(BytesIO(image))
    data = numpy.asarray(image)

    string = ""
    is_str = False

    for row_index, row in enumerate(data):
        for col_index, col in enumerate(row):
            if row_index == 0 and col_index == 0:
                is_str, _, _, _ = col
                print(is_str)
                continue
            for char in col:
                if char == 0:
                    continue
                string += chr(char)

    if is_str:
        return base64.b85decode(string).decode("utf-8")
    return base64.b85decode(string)
