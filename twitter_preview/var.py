import re

STATUS_LINK = "https://twitter.com/{username}/status/{id}"
ENDPOINT = (
    "https://api.twitter.com/2/tweets?ids={ids}"
    "&tweet.fields=text,created_at,public_metrics,entities,possibly_sensitive"
    "&expansions=attachments.media_keys,author_id"
    "&media.fields=preview_image_url,duration_ms,type,url"
    "&user.fields=profile_image_url,protected"
)
SHORT_LINK_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?(t\.co/[a-zA-Z\d_.-]{10})")
STATUS_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?twitter\.com/\w+/status/(\d+)"
)
