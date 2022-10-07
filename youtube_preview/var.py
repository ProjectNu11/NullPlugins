import re

VIDEO_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?youtube.com/watch\?v=([a-zA-Z\d_.-]{11})"
)
SHORT_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(youtu\.be/[a-zA-Z\d_.-]{11})"
)
VIDEO_LINK = "https://www.youtube.com/watch?v={id}"

ENDPOINT = (
    "https://youtube.googleapis.com/youtube/v3/"
    "videos?part=snippet%2CcontentDetails%2Cstatistics"
    "&id={ids}&key={key}"
)
