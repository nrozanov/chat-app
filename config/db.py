from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, create_engine

from config.settings import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"options": "-c timezone=utc"},
)


def get_session() -> Generator[Session, None, None]:  # pragma: no cover
    """
    FastAPI dependency for creating db sessions inside request
    """
    with Session(engine, expire_on_commit=False) as _session:
        yield _session


@contextmanager
def create_session() -> Generator[Session, None, None]:
    """
    Context manager for creating db sessions outside of API request context, e.g.
    in celery tasks or management commands
    """
    return get_session()


class RedisManager():
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RedisManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self._pubsub = None
        self._listen_future = None
        self._callbacks = dict()

    def connect(self):
        redis_url = settings.REDIS_URL
        if settings.REDIS_URL[:6] == 'rediss':
            redis_url += '?ssl_cert_reqs=none'
        
        connection_pool = BlockingConnectionPool.from_url(redis_url, max_connections=settings.REDIS_CONNECTIONS_LIMIT)
        self._redis = Redis(connection_pool=connection_pool)
        self._pubsub = self._redis.pubsub()

    async def disconnect(self):
        active_channels = [key for key in list(self._callbacks.keys()) if self._callbacks[key] is not None]
        if active_channels:
            await self._redis.publish(active_channels[0], STOPWORD)

        if self._listen_future is None:
            return
        await self._listen_future

    async def _start_listening(self):
        while True:
            try:
                async with async_timeout.timeout(1):
                    message = await self._pubsub.get_message(ignore_subscribe_messages=True)
                    if message is not None:
                        message_str = message["data"].decode("utf-8")
                        if message_str == STOPWORD:
                            break

                        channel = message["channel"].decode("utf-8")
                        cb = self._callbacks.get(channel)
                        if cb is not None:
                            await cb(message_str)
                    await asyncio.sleep(0.01)
            except asyncio.TimeoutError:
                pass

    async def publish(self, channel, message):
        await self._redis.publish(channel, message)

    async def subscribe(self, channel, callback):
        try:
            await self._pubsub.subscribe(channel)
        except aioredis.exceptions.ConnectionError:
            self.connect()
            await self._pubsub.subscribe(channel)

        self._callbacks[channel] = callback

        if self._listen_future is None:
            self._listen_future = asyncio.create_task(self._start_listening())

    async def unsubscribe(self, channel):
        if len(self._callbacks) == 1:
            await self._redis.publish(channel, STOPWORD)

        self._callbacks.pop(channel)
        await self._pubsub.unsubscribe(channel)

        if not self._callbacks:
            await self._listen_future
            self._listen_future = None

    def get_cache_value(self, key):
        return self._redis.get(key)

    def set_cache_value(self, key, value):
        return self._redis.set(key, value)


redis_manager = RedisManager()
