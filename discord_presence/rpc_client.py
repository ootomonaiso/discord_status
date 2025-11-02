"""Thin wrapper around pypresence Presence with reconnect handling."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pypresence import Presence


class RPCClient:
    """Manage the RPC connection lifecycle and outgoing payloads."""

    def __init__(self, app_id: str) -> None:
        self.app_id = app_id
        self.rpc: Optional[Presence] = None
        self.connected = False
        self._start_ts: Optional[int] = None

    def connect(self) -> bool:
        """Ensure the RPC connection is alive."""
        if self.connected:
            return True
        try:
            self.rpc = Presence(self.app_id)
            self.rpc.connect()
            self.connected = True
            return True
        except Exception:
            self.connected = False
            self.rpc = None
            return False

    def clear(self) -> None:
        """Clear presence and close the connection."""
        if not self.connected or not self.rpc:
            return
        try:
            self.rpc.clear()
        except Exception:
            pass
        finally:
            try:
                self.rpc.close()
            except Exception:
                pass
            self.connected = False
            self.rpc = None
            self._start_ts = None

    def set_elapsed(self, mode: Optional[str]) -> None:
        """Manage the elapsed timer start/stop."""
        if mode == "start":
            if self._start_ts is None:
                self._start_ts = int(time.time())
        elif mode == "stop":
            self._start_ts = None

    def update(self, presence: Dict[str, Any]) -> bool:
        """Send an update to Discord."""
        if not self.connected and not self.connect():
            return False
        if not self.rpc:
            return False

        payload: Dict[str, Any] = {}
        if presence.get("details"):
            payload["details"] = presence["details"]
        if presence.get("state"):
            payload["state"] = presence["state"]

        assets = presence.get("assets") or {}
        if assets.get("large_image"):
            payload["large_image"] = assets["large_image"]
        if assets.get("small_image"):
            payload["small_image"] = assets["small_image"]

        buttons: List[Dict[str, str]] = presence.get("buttons") or []
        if buttons:
            payload["buttons"] = buttons

        if self._start_ts is not None:
            payload["start"] = self._start_ts

        try:
            self.rpc.update(**payload)
            return True
        except Exception:
            self.connected = False
            return False
