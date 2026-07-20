"""System tray icon manager for Discord Presence daemon."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None  # type: ignore
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore

if TYPE_CHECKING:
    from typing import Any


class TrayIcon:
    """Manages system tray icon and menu."""

    # Presets exposed as quick-select items in the tray "アクティビティ" submenu,
    # paired with the label shown to the user.
    _ACTIVITY_PRESETS = [
        ("work_vscode", "💻 作業中 (VS Code)"),
        ("meeting", "📞 会議中"),
        ("break_short", "☕ 休憩中"),
        ("gaming", "🎮 ゲーム中"),
        ("idle", "⏸️ 待機中"),
    ]

    # Manual status overrides shown in the tray "ステータス" submenu.
    _STATUS_ITEMS = [
        ("available", "✅ 参加OK"),
        ("busy", "🚫 忙しい"),
        ("solo", "🎧 ひとりで"),
    ]

    def __init__(
        self,
        on_quit: Callable[[], None],
        on_toggle_auto: Callable[[], None],
        on_preset_select: Callable[[str], None],
        get_status: Callable[[], dict],
        on_open_config: Optional[Callable[[], None]] = None,
        on_status_select: Optional[Callable[[str], None]] = None,
        on_auto: Optional[Callable[[], None]] = None,
    ) -> None:
        self.on_quit = on_quit
        self.on_toggle_auto = on_toggle_auto
        self.on_preset_select = on_preset_select
        self.on_status_select = on_status_select
        self.on_auto = on_auto
        self.get_status = get_status
        self.on_open_config = on_open_config
        self.icon: Optional[Any] = None
        self._running = False

    def _create_icon_image(self) -> Any:
        """Create a simple icon image."""
        if Image is None or ImageDraw is None:
            return None

        # Create a simple Discord-like icon
        width = 64
        height = 64
        image = Image.new("RGB", (width, height), color=(88, 101, 242))
        draw = ImageDraw.Draw(image)

        # Draw a simple "D" shape
        draw.ellipse([8, 8, 56, 56], fill=(255, 255, 255))
        draw.ellipse([16, 16, 48, 48], fill=(88, 101, 242))
        draw.rectangle([32, 16, 48, 48], fill=(88, 101, 242))

        return image

    def _status(self) -> dict:
        """Fetch the current daemon state, tolerating errors."""
        try:
            return self.get_status() or {}
        except Exception:
            return {}

    def _build_status_menu(self) -> Any:
        """ステータス submenu with a radio dot on the active override."""
        items = [
            pystray.MenuItem(
                "🔄 自動",
                self._select_status("auto"),
                radio=True,
                checked=lambda item: self._status().get("manual_status") is None,
            ),
            pystray.Menu.SEPARATOR,
        ]
        for key, label in self._STATUS_ITEMS:
            items.append(
                pystray.MenuItem(
                    label,
                    self._select_status(key),
                    radio=True,
                    checked=lambda item, k=key: self._status().get("manual_status") == k,
                )
            )
        return pystray.Menu(*items)

    def _build_activity_menu(self) -> Any:
        """アクティビティ submenu with a radio dot on the active preset/auto."""
        items = [
            pystray.MenuItem(
                "🔄 自動検出",
                self._select_auto,
                radio=True,
                checked=lambda item: self._status().get("auto", True),
            ),
            pystray.Menu.SEPARATOR,
        ]
        for key, label in self._ACTIVITY_PRESETS:
            items.append(
                pystray.MenuItem(
                    label,
                    self._select_preset(key),
                    radio=True,
                    checked=lambda item, k=key: (
                        not self._status().get("auto", True)
                        and self._status().get("manual_preset") == k
                    ),
                )
            )
        return pystray.Menu(*items)

    def _get_menu(self) -> Any:
        """Build the tray menu."""
        if pystray is None:
            return None

        status = self._status()
        current_rule = status.get("rule", "未初期化")
        current_preset = status.get("preset", "なし")

        return pystray.Menu(
            pystray.MenuItem(f"現在: {current_preset}", None, enabled=False),
            pystray.MenuItem(f"ルール: {current_rule}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "自動モード",
                self._toggle_auto,
                checked=lambda item: self._status().get("auto", True),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("ステータス", self._build_status_menu()),
            pystray.MenuItem("アクティビティ", self._build_activity_menu()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("設定を開く", self._open_config),
            pystray.MenuItem("終了", self._quit),
        )

    def _refresh(self) -> None:
        """Re-render the menu so radio/check marks reflect the new state."""
        if self.icon:
            self.icon.update_menu()

    def _select_status(self, key: str) -> Callable[..., None]:
        def handler(icon: Any = None, item: Any = None) -> None:
            if self.on_status_select:
                self.on_status_select(key)
            self._refresh()
        return handler

    def _select_preset(self, key: str) -> Callable[..., None]:
        def handler(icon: Any = None, item: Any = None) -> None:
            self.on_preset_select(key)
            self._refresh()
        return handler

    def _select_auto(self, icon: Any = None, item: Any = None) -> None:
        # Prefer the dedicated "force auto" callback; fall back to toggle.
        if self.on_auto:
            self.on_auto()
        else:
            self.on_toggle_auto()
        self._refresh()

    def _toggle_auto(self, icon: Any = None, item: Any = None) -> None:
        """Toggle automatic rule evaluation."""
        self.on_toggle_auto()
        if self.icon:
            self.icon.update_menu()

    def _open_config(self, icon: Any = None, item: Any = None) -> None:
        """Open config editor."""
        if self.on_open_config:
            self.on_open_config()

    def _quit(self, icon: Any = None, item: Any = None) -> None:
        """Quit the application."""
        self.on_quit()
        if self.icon:
            self.icon.stop()

    def run(self) -> None:
        """Start the tray icon (blocking)."""
        if pystray is None:
            raise RuntimeError("pystray が利用できません。pip install pystray でインストールしてください。")

        self._running = True
        image = self._create_icon_image()
        self.icon = pystray.Icon(
            "discord_presence",
            image,
            "Discord Rich Presence",
            menu=self._get_menu(),
        )
        self.icon.run()

    def run_detached(self) -> threading.Thread:
        """Start the tray icon in a background thread."""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread

    def update_menu(self) -> None:
        """Update the tray menu."""
        if self.icon:
            self.icon.menu = self._get_menu()
            self.icon.update_menu()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()
