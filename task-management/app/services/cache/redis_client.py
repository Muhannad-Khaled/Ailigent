"""Redis client for caching and job queue."""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper."""

    _instance: Optional["RedisClient"] = None
    _redis: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._redis is not None:
            return

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(
                "Unable to connect to Redis",
                details={"error": str(e)},
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._redis:
            await self.connect()
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value with optional TTL in seconds."""
        if not self._redis:
            await self.connect()
        try:
            if ttl:
                await self._redis.setex(key, ttl, value)
            else:
                await self._redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set JSON value with optional TTL."""
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Redis SET JSON error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key."""
        if not self._redis:
            await self.connect()
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._redis:
            await self.connect()
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern."""
        if not self._redis:
            await self.connect()
        try:
            return await self._redis.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
            return []

    async def ttl(self, key: str) -> int:
        """Get TTL for key in seconds."""
        if not self._redis:
            await self.connect()
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -1

    async def flush_all(self) -> bool:
        """Flush all keys (use with caution)."""
        if not self._redis:
            await self.connect()
        try:
            await self._redis.flushall()
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHALL error: {e}")
            return False

    async def health_check(self) -> dict:
        """Check Redis connection health."""
        try:
            if not self._redis:
                await self.connect()
            await self._redis.ping()
            info = await self._redis.info("server")
            return {
                "connected": True,
                "redis_version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }


_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get the singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client
