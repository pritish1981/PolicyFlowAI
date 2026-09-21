from redis import Redis

from app.core.config import settings

redis_client = Redis.from_url(
    settings.redis_url,
    socket_connect_timeout=settings.redis_connect_timeout_seconds,
    socket_timeout=settings.redis_socket_timeout_seconds,
    decode_responses=True,
)
