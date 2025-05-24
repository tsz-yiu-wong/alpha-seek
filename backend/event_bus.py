import asyncio
import json
import traceback
import aioredis
from aioredis import Redis
import logging
import collections

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self, redis_url="redis://localhost"):
        self.redis_url = redis_url
        self._redis: Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._callbacks = collections.defaultdict(list)
        self._listener_tasks = {}
        self._connect_task = None # Task to manage initial connection

    async def _ensure_connected(self):
        """确保连接已建立，如果未连接则尝试连接一次。"""
        if self._redis and await self._redis.ping():
             return
        if self._connect_task and not self._connect_task.done():
             await self._connect_task # Wait for ongoing connection attempt
             if self._redis: return # Check if successful

        # Start connection attempt
        self._connect_task = asyncio.create_task(self._connect())
        try:
            await self._connect_task
            if not self._redis: # Check if connection was successful
                 raise ConnectionError("Failed to connect after attempt.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}", exc_info=True)
            self._connect_task = None # Reset task if connection fails
            raise ConnectionError(f"Redis connection failed: {e}")

    async def _connect(self):
        """尝试连接 Redis 并设置 pubsub。"""
        try:
            logger.info(f"Connecting to Redis at {self.redis_url}...")
            # Close existing connections if any before creating new ones
            if self._pubsub: await self._pubsub.close()
            if self._redis: await self._redis.close()

            self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            self._pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
            logger.info("Connected to Redis.")
        except Exception as e:
            logger.error(f"Failed to connect/initialize Redis: {e}", exc_info=True)
            self._redis = None
            self._pubsub = None
            # Do not raise here, let _ensure_connected handle it

    async def _listen(self, channel: str):
        """监听单个 Redis 频道。"""
        # Assumes connection is okay when task starts
        if not self._pubsub:
             logger.error(f"Cannot listen on '{channel}', pubsub not ready.")
             return # Exit if pubsub is not available

        try:
            await self._pubsub.subscribe(channel)
            logger.info(f"Listener started for Redis channel '{channel}'.")
            async for message in self._pubsub.listen():
                if message and message["type"] == "message" and message["channel"] == channel:
                    try:
                        data = json.loads(message["data"])
                        # Call all registered callbacks for this channel concurrently
                        tasks = [
                             asyncio.create_task(self._safe_callback(callback, channel, data))
                             for callback in self._callbacks.get(channel, []) # Use .get for safety
                        ]
                        if tasks: await asyncio.gather(*tasks, return_exceptions=True) # Log errors in _safe_callback
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error on channel '{channel}': {message['data'][:100]}...") # Log snippet
                    except Exception as e:
                        logger.error(f"Error processing message for '{channel}': {e}", exc_info=True)
        except asyncio.CancelledError:
             logger.info(f"Listener task for '{channel}' cancelled.")
        except (aioredis.ConnectionError, ConnectionRefusedError) as e:
             logger.error(f"Redis connection error in listener '{channel}': {e}. Task stopping.")
             self._listener_tasks.pop(channel, None) # Remove broken task
             # Simple handling: requires manual restart or intervention
        except Exception as e:
            logger.error(f"Unexpected listener error for '{channel}': {e}. Task stopping.", exc_info=True)
            self._listener_tasks.pop(channel, None) # Remove broken task
        finally:
            # Attempt to clean up Redis subscription when listener stops/exits
            if self._pubsub:
                try: await self._pubsub.unsubscribe(channel)
                except Exception: pass # Ignore errors during cleanup

    async def _safe_callback(self, callback, channel, data):
         """安全地执行回调（始终异步化），记录错误。"""
         callback_name = getattr(callback, '__name__', 'unknown')
         try:
              if asyncio.iscoroutinefunction(callback):
                   await callback(channel, data)
              else:
                   # Run sync callback in default executor to avoid blocking event loop heavily
                   # Note: This adds complexity back, maybe just use create_task?
                   # For simplicity let's try running sync directly but warn if it blocks.
                   # loop = asyncio.get_running_loop()
                   # await loop.run_in_executor(None, callback, channel, data)
                   callback(channel, data) # Direct call (potential blocking)
         except Exception as e:
              logger.error(f"Error in callback '{callback_name}' for channel '{channel}': {e}", exc_info=True)


    async def subscribe(self, channel: str, callback):
        """订阅频道。"""
        await self._ensure_connected() # Ensure connection first

        if callback not in self._callbacks[channel]:
            self._callbacks[channel].append(callback)
            logger.info(f"Callback {getattr(callback, '__name__', 'unknown')} registered for channel '{channel}'.")
            # Start listener task only if it doesn't exist
            if channel not in self._listener_tasks:
                if self._pubsub: # Check again if pubsub is ready
                     task = asyncio.create_task(self._listen(channel))
                     self._listener_tasks[channel] = task
                else:
                     logger.error(f"Cannot start listener for '{channel}', pubsub unavailable after connect attempt.")
                     # Rollback or raise? Let's just log for lightweight version.
                     # self._callbacks[channel].remove(callback)


    async def unsubscribe(self, channel: str, callback):
        """取消订阅频道。"""
        if channel in self._callbacks and callback in self._callbacks[channel]:
            self._callbacks[channel].remove(callback)
            logger.info(f"Callback {getattr(callback, '__name__', 'unknown')} unregistered from '{channel}'.")
            # If no callbacks left, stop the listener task
            if not self._callbacks[channel]:
                 task = self._listener_tasks.pop(channel, None)
                 if task:
                      task.cancel()
                      logger.info(f"Stopped listener task for '{channel}'.")
                 # Clean up empty list from dict
                 if channel in self._callbacks:
                     del self._callbacks[channel]


    async def publish(self, channel: str, data):
        """发布消息到频道。"""
        try:
            await self._ensure_connected() # Ensure connection
            data_str = json.dumps(data)
            await self._redis.publish(channel, data_str)
        except ConnectionError as e:
             logger.error(f"Publish failed on '{channel}', connection error: {e}")
        except TypeError as e: # JSON serialization error
             logger.error(f"Publish failed on '{channel}', serialization error: {e}. Data: {data}", exc_info=True)
        except Exception as e:
             logger.error(f"Publish failed on '{channel}': {e}", exc_info=True)


    async def close(self):
        """关闭连接并清理任务。"""
        logger.info("Closing EventBus...")
        # Cancel listeners
        for task in self._listener_tasks.values():
            task.cancel()
        if self._listener_tasks:
             await asyncio.gather(*self._listener_tasks.values(), return_exceptions=True) # Wait briefly
        self._listener_tasks.clear()
        self._callbacks.clear()

        # Close connections
        if self._pubsub:
             try: await self._pubsub.close()
             except Exception: pass
        if self._redis:
            try:
                 await self._redis.close()
                 # Ensure pool is disconnected if applicable (aioredis handles this mostly)
                 if hasattr(self._redis, 'connection_pool'):
                     await self._redis.connection_pool.disconnect()
            except Exception: pass
        logger.info("EventBus closed.") 