"""Tracks pending Meta AI requests, collecting multi-chunk responses.

Meta AI identifiers (per whatsmeow Go source types/jid.go):
  Old:  MetaAIJID    = "13135550002"@s.whatsapp.net
  New:  NewMetaAIJID = "867051314767696"@bot    (personal)
  Biz:  "718584497008509"@bot                     (business)
"""

import asyncio
import os
from collections import OrderedDict

META_AI_PHONE = os.getenv("META_AI_PHONE", "13135550002")  # legacy override
META_AI_JID = f"{META_AI_PHONE}@s.whatsapp.net"

# Maps request_id → asyncio.Queue — each chunk is put() into the queue.
# Sentinel None signals end-of-stream (used to unblock collector on timeout).
_pending: OrderedDict[str, asyncio.Queue] = OrderedDict()


def set_pending(request_id: str, queue: asyncio.Queue) -> None:
    _pending[request_id] = queue


def push_chunk(payload: dict) -> bool:
    """Called for every Meta AI message. Pushes payload into the oldest pending queue."""
    if not _pending:
        return False
    key, queue = next(iter(_pending.items()))
    queue.put_nowait(payload)
    return True


def has_pending() -> bool:
    return bool(_pending)


def cleanup(request_id: str) -> None:
    _pending.pop(request_id, None)


def cleanup_done() -> None:
    pass  # kept for backwards compat
