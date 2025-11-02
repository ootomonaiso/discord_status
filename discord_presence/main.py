"""Entry point for the Discord Rich Presence daemon."""

from __future__ import annotations

import json
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Support both direct execution and module execution
if __name__ == "__main__" and __package__ is None:
    # Direct execution: add parent to sys.path and use absolute imports
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from discord_presence.rpc_client import RPCClient
    from discord_presence.rules import RuleEngine
    from discord_presence.sensors import take_snapshot
    from discord_presence.tray import TrayIcon
else:
    # Module execution: use relative imports
    from .rpc_client import RPCClient
    from .rules import RuleEngine
    from .sensors import take_snapshot
    from .tray import TrayIcon


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


def main() -> None:
    # When running as a PyInstaller bundle, use the executable's directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base = Path(sys.executable).parent
    else:
        # Running as script
        base = Path(__file__).resolve().parent.parent
    
    cfg_path = base / "config.yaml"
    if not cfg_path.exists():
        print(f"[エラー] config.yaml が見つかりません: {cfg_path}")
        sys.exit(1)

    cfg = load_config(cfg_path)
    app_id = str(cfg.get("options", {}).get("app_id") or "").strip()
    if not app_id or app_id == "YOUR_DISCORD_APP_ID":
        print("[エラー] config.yaml の options.app_id を設定してください。")
        sys.exit(1)

    timing = cfg.get("timing", {})
    debounce_ms = int(timing.get("debounce_ms", 3000))
    min_update_sec = int(timing.get("min_update_sec", 15))
    backoff_seq = list(timing.get("reconnect_backoff", [1, 2, 5, 10, 20]))
    
    # AFK detection threshold
    afk_idle_sec = int(cfg.get("options", {}).get("afk_idle_sec", 1800))
    print(f"[情報] 寝落ち検出: {afk_idle_sec}秒 ({afk_idle_sec // 60}分) 以上のアイドルで表示")
    
    # Steam library paths for game detection
    steam_paths = cfg.get("options", {}).get("steam_library_paths", [])
    if steam_paths:
        print(f"[情報] Steamライブラリパス: {len(steam_paths)}個設定済み")
        for path in steam_paths:
            print(f"  - {path}")

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
            print("[情報] 自動モードを有効にしました")
        else:
            print("[情報] 自動モードを無効にしました")

    def on_preset_select(preset_name: str) -> None:
        nonlocal auto_mode, manual_preset
        auto_mode = False
        manual_preset = preset_name
        print(f"[情報] 手動でプリセット '{preset_name}' を選択しました")

    def on_status_select(status: str) -> None:
        """Set manual status override (available/busy/solo/auto)"""
        nonlocal manual_status
        if status == "auto":
            manual_status = None
            print("[情報] ステータスを自動に設定しました")
        else:
            manual_status = status
            status_names = {
                "available": "参加OK",
                "busy": "忙しい",
                "solo": "ひとりで"
            }
            print(f"[情報] ステータスを '{status_names.get(status, status)}' に設定しました")

    def get_status() -> tuple[bool, str, str]:
        status_info = f"{last_rule or '未初期化'} | ステータス: {manual_status or '自動'}"
        return (auto_mode, status_info, last_preset or "なし")

    def on_open_config() -> None:
        """Open config editor in a subprocess."""
        import subprocess
        import os
        config_editor_path = base / "config_editor.py"
        python_exe = sys.executable
        try:
            # Use CREATE_NO_WINDOW flag on Windows to avoid showing console
            if os.name == "nt":
                subprocess.Popen(
                    [python_exe, str(config_editor_path)],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                subprocess.Popen([python_exe, str(config_editor_path)])
            print("[情報] 設定エディタを起動しました")
        except Exception as e:
            print(f"[エラー] 設定エディタの起動に失敗: {e}")

    # Start tray icon
    try:
        tray = TrayIcon(on_quit, on_toggle_auto, on_preset_select, get_status, on_open_config, on_status_select)
        tray_thread = tray.run_detached()
        print("[情報] タスクトレイアイコンを起動しました")
    except Exception as e:
        print(f"[警告] タスクトレイアイコンの起動に失敗: {e}")
        print("[情報] コンソールモードで続行します。Ctrl+C で終了してください。")
        tray = None

    print("[情報] 前面アプリとアイドル時間の監視を開始しました")

    while not shutting_down:
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
                # Build presence from manual preset - import at top level
                # Note: _apply_template is already imported via rules module
                try:
                    if __package__ is None:
                        from discord_presence.rules import _apply_template
                    else:
                        from .rules import _apply_template  # type: ignore
                except ImportError:
                    def _apply_template(s, ctx):  # type: ignore
                        if s is None:
                            return None
                        try:
                            return s.format_map({k: ("" if v is None else v) for k, v in ctx.items()})
                        except Exception:
                            return s
                
                details = _apply_template(preset_data.get("details"), context)
                state = _apply_template(preset_data.get("state"), context)
                candidate = {
                    "details": details,
                    "state": state,
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
            print(f"[警告] Discord RPC に接続できません。{wait}秒後に再試行します。")
            time.sleep(wait)
            continue

        backoff_idx = 0

        if should_apply and (diff or cooldown_ok):
            if auto_mode and elapsed_mode:
                rpc.set_elapsed(elapsed_mode)
            if rpc.update(candidate):
                last_payload = candidate
                last_sent_ts = time.time()
                print(
                    f"[情報] 更新: ルール={current_rule} プリセット={current_preset} "
                    f"details={candidate.get('details')!r} state={candidate.get('state')!r}"
                )
            else:
                print("[警告] Presence の更新に失敗しました。再試行します。")

        time.sleep(0.5)

    print("[情報] 終了処理中: Presence をクリアします。")
    try:
        rpc.clear()
    finally:
        if tray:
            tray.stop()
        print("[情報] 終了しました。")


if __name__ == "__main__":
    main()
