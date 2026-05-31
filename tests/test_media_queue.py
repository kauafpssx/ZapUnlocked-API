"""Tests for the serialised TaskQueue."""

import pytest

from src.services.media.queue import TaskQueue


class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue_returns_result(self):
        queue = TaskQueue()
        result = await queue.enqueue(self._dummy_coro(42))
        assert result == 42

    @pytest.mark.asyncio
    async def test_enqueue_raises_on_error(self):
        queue = TaskQueue()

        async def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await queue.enqueue(failing())

    @pytest.mark.asyncio
    async def test_serialises_concurrent_tasks(self):
        queue = TaskQueue()
        order = []

        async def task_a():
            order.append("a_start")
            await asyncio.sleep(0.05)
            order.append("a_end")
            return "A"

        async def task_b():
            order.append("b_start")
            await asyncio.sleep(0.02)
            order.append("b_end")
            return "B"

        import asyncio
        results = await asyncio.gather(
            queue.enqueue(task_a()),
            queue.enqueue(task_b()),
        )
        assert set(results) == {"A", "B"}
        assert order == ["a_start", "a_end", "b_start", "b_end"]

    async def _dummy_coro(self, value):
        return value
