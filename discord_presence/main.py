"""Entry point for the Discord Rich Presence daemon."""

from __future__ import annotations

import json
import logging
import signal
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

# Support both direct execution and module execution
if __name__ == "__main__" and __package__ is None:
    # Direct execution: add parent to sys.path and use absolute imports
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from discord_presence.rpc_client import RPCClient
    from discord_presence.rules import RuleEngine, _apply_template
    from discord_presence.sensors import take_snapshot
    from discord_presence.tray import TrayIcon
else:
    # Module execution: use relative imports
    from .rpc_client import RPCClient
    from .rules import RuleEngine, _apply_template
    from .sensors import take_snapshot
    from .tray import TrayIcon

logger = logging.getLogger(__name__)


def _basic_logging(debug: bool, log_path: Optional[Path] = None) -> None:
    """Configure logging once. DEBUG surfaces our own sensor/RPC diagnostics
    without drowning in third-party (PIL/asyncio) debug spam. When log_path is
    given, also write to a rotating file so the windowed exe leaves a trail."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    if debug:
        # Only elevate our own loggers; "__main__" covers the frozen entrypoint.
        for name in ("discord_presence", "__main__"):
            logging.getLogger(name).setLevel(logging.DEBUG)
        for noisy in ("PIL", "asyncio", "pystray"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    if log_path is not None:
        root = logging.getLogger()
        already = any(
            isinstance(h, RotatingFileHandler) and getattr(h, "_dp_log", False)
            for h in root.handlers
        )
        if not already:
            try:
                fh = RotatingFileHandler(
                    log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
                )
                fh.setFormatter(logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                ))
                fh._dp_log = True  # type: ignore[attr-defined]
                root.addHandler(fh)
            except Exception:
                pass  # File logging is best-effort; never block startup.


def load_config(path: Path) -> Dict[str, Any]:
    try:
        yaml = __import__("yaml")
    except ModuleNotFoundError:
        print("[error] Missing dependency: PyYAML (install with 'pip install pyyaml').")
        sys.exit(1)

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def presence_to_dict(spec) -> Dict[str, Any]:
    return {
        "details": spec.details,
        "state": spec.state,
        "assets": spec.assets,
        "buttons": spec.buttons,
    }


def _open_editor(base: Path) -> None:
    """Launch the config editor GUI (used for the bundled '--config' entry)."""
    _basic_logging(False)
    try:
        from config_editor import ConfigEditor
    except Exception:  # pragma: no cover - depends on bundling/path
        from ..config_editor import ConfigEditor  # type: ignore
    ConfigEditor(base / "config.yaml").run()


def main() -> None:
    # When running as a PyInstaller bundle, use the executable's directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base = Path(sys.executable).parent
    else:
        # Running as script
        base = Path(__file__).resolve().parent.parent

    # Allow the single bundled exe to double as the config editor launcher.
    if "--config" in sys.argv:
        _open_editor(base)
        return

    log_path = base / "discord_presence.log"
    cfg_path = base / "config.yaml"
    if not cfg_path.exists():
        _basic_logging(False, log_path)
        logger.error("config.yaml が見つかりません: %s", cfg_path)
        sys.exit(1)

    cfg = load_config(cfg_path)
    options = cfg.get("options", {})

    _basic_logging(bool(options.get("debug", False)), log_path)

    app_id = str(options.get("app_id") or "").strip()
    if not app_id or app_id == "YOUR_DISCORD_APP_ID":
        logger.error("config.yaml の options.app_id を設定してください。")
        sys.exit(1)

    timing = cfg.get("timing", {})
    debounce_ms = int(timing.get("debounce_ms", 3000))
    min_update_sec = int(timing.get("min_update_sec", 15))
    backoff_seq = list(timing.get("reconnect_backoff", [1, 2, 5, 10, 20]))

    # AFK detection threshold
    afk_idle_sec = int(options.get("afk_idle_sec", 1800))
    logger.info("寝落ち検出: %d秒 (%d分) 以上のアイドルで表示", afk_idle_sec, afk_idle_sec // 60)

    # Steam library paths for game detection
    steam_paths = options.get("steam_library_paths", [])
    if steam_paths:
        logger.info("Steamライブラリパス: %d個設定済み", len(steam_paths))
        for path in steam_paths:
            logger.info("  - %s", path)

    engine = RuleEngine(cfg)
    rpc = RPCClient(app_id)

    shutting_down = False
    auto_mode = True
    manual_preset: Optional[str] = None
    manual_status: Optional[str] = None  # "available", "busy", "solo", or None for auto

    def _graceful(*_: object) -> None:
        nonlocal shutting_down
        shutting_down = True

    signal.signal(signal.SIGINT, _graceful)
    signal.signal(signal.SIGTERM, _graceful)

    last_rule: Optional[str] = None
    last_preset: Optional[str] = None
    stable_since_ms: Optional[int] = None
    last_payload: Optional[Dict[str, Any]] = None
    last_sent_ts = 0.0
    backoff_idx = 0

    # Tray icon callbacks
    def on_quit() -> None:
        nonlocal shutting_down
        shutting_down = True

    def on_toggle_auto() -> None:
        nonlocal auto_mode, manual_preset
        auto_mode = not auto_mode
        if auto_mode:
            manual_preset = None
            logger.info("自動モードを有効にしました")
        else:
            logger.info("自動モードを無効にしました")

    def on_auto() -> None:
        """Force automatic mode (used by the tray '自動検出' item)."""
        nonlocal auto_mode, manual_preset
        auto_mode = True
        manual_preset = None
        logger.info("自動モードを有効にしました")

    def on_preset_select(preset_name: str) -> None:
        nonlocal auto_mode, manual_preset
        auto_mode = False
        manual_preset = preset_name
        logger.info("手動でプリセット '%s' を選択しました", preset_name)

    def on_status_select(status: str) -> None:
        """Set manual status override (available/busy/solo/auto)"""
        nonlocal manual_status
        if status == "auto":
            manual_status = None
            logger.info("ステータスを自動に設定しました")
        else:
            manual_status = status
            status_names = {
                "available": "参加OK",
                "busy": "忙しい",
                "solo": "ひとりで",
            }
            logger.info("ステータスを '%s' に設定しました", status_names.get(status, status))

    def get_status() -> Dict[str, Any]:
        return {
            "auto": auto_mode,
            "rule": last_rule or "未初期化",
            "preset": last_preset or "なし",
            "manual_status": manual_status,
            "manual_preset": manual_preset,
        }

    def on_open_config() -> None:
        """Open config editor in a subprocess."""
        import subprocess
        import os
        if getattr(sys, "frozen", False):
            # The bundled exe launches itself with --config to show the editor.
            cmd = [sys.executable, "--config"]
        else:
            cmd = [sys.executable, str(base / "config_editor.py")]
        try:
            # Use CREATE_NO_WINDOW flag on Windows to avoid showing console
            if os.name == "nt":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(cmd)
            logger.info("設定エディタを起動しました")
        except Exception as e:
            logger.error("設定エディタの起動に失敗: %s", e)

    # Start tray icon
    try:
        tray = TrayIcon(on_quit, on_toggle_auto, on_preset_select, get_status, on_open_config, on_status_select, on_auto)
        tray_thread = tray.run_detached()
        logger.info("タスクトレイアイコンを起動しました")
    except Exception as e:
        logger.warning("タスクトレイアイコンの起動に失敗: %s", e)
        logger.info("コンソールモードで続行します。Ctrl+C で終了してください。")
        tray = None

    logger.info("前面アプリとアイドル時間の監視を開始しました")

    try:
        cfg_mtime = cfg_path.stat().st_mtime
    except OSError:
        cfg_mtime = 0.0

    while not shutting_down:
        # Hot-reload config when the file changes (e.g. saved from the editor),
        # so edits take effect without restarting the daemon.
        try:
            current_mtime = cfg_path.stat().st_mtime
        except OSError:
            current_mtime = cfg_mtime
        if current_mtime != cfg_mtime:
            cfg_mtime = current_mtime
            try:
                cfg = load_config(cfg_path)
                options = cfg.get("options", {})
                engine = RuleEngine(cfg)
                steam_paths = options.get("steam_library_paths", [])
                timing = cfg.get("timing", {})
                debounce_ms = int(timing.get("debounce_ms", 3000))
                min_update_sec = int(timing.get("min_update_sec", 15))
                last_payload = None  # Force a fresh push with the new settings.
                logger.info("設定を再読み込みしました")
            except Exception as exc:
                logger.error("設定の再読み込みに失敗: %s", exc)

        snapshot = take_snapshot(steam_paths)

        # Determine which preset to use for activity
        if auto_mode:
            # Automatic mode: use rule engine
            evaluation = engine.evaluate(snapshot)
            candidate = presence_to_dict(evaluation.presence)
            current_rule = evaluation.name
            current_preset = evaluation.preset_name
            elapsed_mode = evaluation.presence.elapsed
        else:
            # Manual mode: use selected preset
            if manual_preset and manual_preset in engine.presets:
                preset_data = engine.presets[manual_preset]
                context = {
                    "window_title": snapshot.window_title or "",
                    "foreground_exe": snapshot.foreground_exe or "",
                    "workspace": "",
                    "idle_sec": snapshot.idle_sec,
                }
                candidate = {
                    "details": _apply_template(preset_data.get("details"), context),
                    "state": _apply_template(preset_data.get("state"), context),
                    "assets": preset_data.get("assets"),
                    "buttons": preset_data.get("buttons"),
                }
                current_rule = "手動"
                current_preset = manual_preset
                elapsed_mode = None
            else:
                # No valid preset in manual mode, skip
                time.sleep(0.5)
                continue
        
        # Apply manual status override if set
        if manual_status:
            status_map = {
                "available": {"state": "参加OK - いつでも声かけてね"},
                "busy": {"state": "参加NG - 集中中"},
                "solo": {"state": "参加NG - ソロタイム"},
            }
            if manual_status in status_map:
                # Override only the state, keep the activity details
                override = status_map[manual_status]
                if "state" in override:
                    candidate["state"] = override["state"]

        # Update status
        if current_rule != last_rule or current_preset != last_preset:
            last_rule = current_rule
            last_preset = current_preset
            stable_since_ms = int(time.time() * 1000)
            if tray:
                tray.update_menu()

        now_ms = int(time.time() * 1000)
        stable_ms = now_ms - (stable_since_ms or now_ms)
        should_apply = stable_ms >= debounce_ms

        diff = json.dumps(candidate, sort_keys=True, ensure_ascii=False) != json.dumps(
            last_payload or {}, sort_keys=True, ensure_ascii=False
        )
        cooldown_ok = (time.time() - last_sent_ts) >= min_update_sec

        if not rpc.connect():
            wait = backoff_seq[min(backoff_idx, len(backoff_seq) - 1)]
            backoff_idx += 1
            logger.warning("Discord RPC に接続できません。%d秒後に再試行します。", wait)
            time.sleep(wait)
            continue

        backoff_idx = 0

        if should_apply and (diff or cooldown_ok):
            if auto_mode and elapsed_mode:
                rpc.set_elapsed(elapsed_mode)
            if rpc.update(candidate):
                last_payload = candidate
                last_sent_ts = time.time()
                logger.info(
                    "更新: ルール=%s プリセット=%s details=%r state=%r",
                    current_rule, current_preset,
                    candidate.get("details"), candidate.get("state"),
                )
            else:
                logger.warning("Presence の更新に失敗しました。再試行します。")

        time.sleep(0.5)

    logger.info("終了処理中: Presence をクリアします。")
    try:
        rpc.clear()
    finally:
        if tray:
            tray.stop()
        logger.info("終了しました。")


if __name__ == "__main__":
    main()
