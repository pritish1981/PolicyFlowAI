from redis import Redis

from app.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    socket_connect_timeout=3,
    socket_timeout=3,
    decode_responses=True,
)
