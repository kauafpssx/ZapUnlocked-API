"""
Serialised task queue for media processing.

Uses an asyncio.Lock to ensure only one media task runs at a time,
preventing resource exhaustion from concurrent FFmpeg invocations.
"""

import asyncio
from src.utils.logger import logger


class TaskQueue:
    def __init__(self):
        self.lock = asyncio.Lock()

    async def enqueue(self, coro):
        """Enqueue a coroutine (serializes execution via Lock)."""
        async with self.lock:
            try:
                return await coro
            except Exception as e:
                logger.error(f"❌ Task queue processing error: {str(e)}")
                raise e


task_queue = TaskQueue()
