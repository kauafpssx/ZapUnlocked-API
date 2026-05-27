import asyncio
from src.utils.logger import logger

class TaskQueue:
    def __init__(self):
        self.lock = asyncio.Lock()

    async def enqueue(self, coro):
        """
        Adiciona uma corrotina à fila (na prática, serializa com Lock)
        """
        async with self.lock:
            try:
                return await coro
            except Exception as e:
                import traceback
                logger.error(f"❌ Erro na fila de processamento: {str(e)}")
                logger.error(traceback.format_exc())
                raise e

task_queue = TaskQueue()
