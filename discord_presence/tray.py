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

    def __init__(
        self,
        on_quit: Callable[[], None],
        on_toggle_auto: Callable[[], None],
        on_preset_select: Callable[[str], None],
        get_status: Callable[[], tuple[bool, str, str]],
        on_open_config: Optional[Callable[[], None]] = None,
        on_status_select: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.on_quit = on_quit
        self.on_toggle_auto = on_toggle_auto
        self.on_preset_select = on_preset_select
        self.on_status_select = on_status_select
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

    def _get_menu(self) -> Any:
        """Build the tray menu."""
        if pystray is None:
            return None

        auto_enabled, current_rule, current_preset = self.get_status()

        return pystray.Menu(
            pystray.MenuItem(
                f"現在: {current_preset}",
                lambda: None,
                enabled=False,
            ),
            pystray.MenuItem(
                f"ルール: {current_rule}",
                lambda: None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "自動切替",
                self._toggle_auto,
                checked=lambda item: auto_enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "ステータス",
                pystray.Menu(
                    pystray.MenuItem(
                        "🔄 自動",
                        lambda: self.on_status_select("auto") if self.on_status_select else None,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        "✅ 参加OK",
                        lambda: self.on_status_select("available") if self.on_status_select else None,
                    ),
                    pystray.MenuItem(
                        "🚫 忙しい",
                        lambda: self.on_status_select("busy") if self.on_status_select else None,
                    ),
                    pystray.MenuItem(
                        "🎧 ひとりで",
                        lambda: self.on_status_select("solo") if self.on_status_select else None,
                    ),
                ),
            ),
            pystray.MenuItem(
                "アクティビティ",
                pystray.Menu(
                    pystray.MenuItem(
                        "🔄 自動検出",
                        lambda: self.on_toggle_auto(),
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        "💻 作業中 (VS Code)",
                        lambda: self.on_preset_select("work_vscode"),
                    ),
                    pystray.MenuItem(
                        "📞 会議中",
                        lambda: self.on_preset_select("meeting"),
                    ),
                    pystray.MenuItem(
                        "☕ 休憩中",
                        lambda: self.on_preset_select("break_short"),
                    ),
                    pystray.MenuItem(
                        "🎮 ゲーム中",
                        lambda: self.on_preset_select("gaming"),
                    ),
                    pystray.MenuItem(
                        "⏸️ 待機中",
                        lambda: self.on_preset_select("idle"),
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("設定を開く", self._open_config),
            pystray.MenuItem("終了", self._quit),
        )

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
