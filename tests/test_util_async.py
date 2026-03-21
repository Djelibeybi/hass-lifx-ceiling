"""Async tests for LIFX utility helpers."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from custom_components.lifx_ceiling.util import async_execute_lifx


@pytest.mark.asyncio
async def test_async_execute_lifx_returns_messages_from_callbacks() -> None:
    """Successful LIFX calls should resolve with their callback messages."""
    message = object()

    def _method(*, callb):
        callb(None, message)

    results = await async_execute_lifx(_method, attempts=1, overall_timeout=0.01)

    assert results == [message]


@pytest.mark.asyncio
async def test_async_execute_lifx_raises_timeout_for_unanswered_methods() -> None:
    """Unanswered LIFX calls should raise TimeoutError."""
    method = Mock()

    with pytest.raises(TimeoutError, match=r"1 requests timed out after 0 seconds\."):
        await async_execute_lifx(method, attempts=1, overall_timeout=0)

    method.assert_called_once()
