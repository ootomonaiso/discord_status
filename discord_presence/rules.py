"""Rule evaluation for presence selection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Support both direct and module imports
try:
    from .sensors import Snapshot
except ImportError:
    from sensors import Snapshot  # type: ignore


@dataclass
class PresenceSpec:
    details: Optional[str] = None
    state: Optional[str] = None
    assets: Optional[Dict[str, str]] = None
    buttons: Optional[List[Dict[str, str]]] = None
    elapsed: Optional[str] = None  # "start" | "stop" | None


@dataclass
class RuleResult:
    name: str
    preset_name: str
    presence: PresenceSpec


def _safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


def _match_regex(pattern: str, value: str) -> bool:
    if not value:
        return False
    return bool(_compile(pattern).search(value))


def _match_any(pattern: str, values: List[str]) -> bool:
    regex = _compile(pattern)
    return any(regex.search(v) for v in values)


def _infer_workspace(title: str) -> str:
    if not title:
        return ""
    parts = re.split(r"\s-\sVisual Studio Code(?:\s-\sInsiders)?", title)
    if len(parts) >= 2:
        left = parts[0]
        segments = re.split(r"\s[—-]\s", left)
        return segments[-1].strip() if segments else left.strip()
    if " - " in title:
        return title.split(" - ")[0].strip()
    return ""


def _apply_template(template: Optional[str], context: Dict[str, Any]) -> Optional[str]:
    if template is None:
        return None
    try:
        return template.format_map({k: ("" if v is None else v) for k, v in context.items()})
    except Exception:
        return template


class RuleEngine:
    """Evaluate rules and build presence payloads."""

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.presets: Dict[str, Dict[str, Any]] = cfg.get("presets", {})
        self.rules: List[Dict[str, Any]] = cfg.get("rules", [])
        self.fallback: Dict[str, Any] = cfg.get("fallback", {"preset": "idle"})
        self.https_only = bool(_safe_get(cfg, "options.https_only_buttons", True))
        # User-defined exe -> display-name catalog for tracking extra apps.
        # e.g. {"obs64.exe": "OBS Studio"}. Keys are treated as regex.
        self.apps: Dict[str, Any] = cfg.get("apps", {}) or {}

    def _match_app(self, exe: str) -> Optional[str]:
        """Return the display name if the foreground exe is a tracked app."""
        if not exe:
            return None
        for pattern, label in self.apps.items():
            if _match_regex(str(pattern), exe):
                return str(label)
        return None

    def evaluate(self, snap: Snapshot) -> RuleResult:
        # Prioritize Steam detection if available
        game_name = ""
        if snap.is_steam_game and snap.detected_game_name:
            game_name = snap.detected_game_name
        elif snap.processes:
            # Fallback to process name detection
            try:
                from .sensors import _detect_game_name
            except ImportError:
                from sensors import _detect_game_name  # type: ignore
            
            for proc in snap.processes:
                if any(pattern in proc.lower() for pattern in [
                    'game', 'elden', 'sekiro', 'darksouls', 'overwatch',
                    'valorant', 'cs2', 'csgo', 'apex', 'fortnite', 'minecraft', 'league'
                ]):
                    game_name = _detect_game_name(proc, snap.processes)
                    break
        
        context = {
            "window_title": snap.window_title or "",
            "foreground_exe": snap.foreground_exe or "",
            "workspace": _infer_workspace(snap.window_title),
            "idle_sec": snap.idle_sec,
            "game_name": game_name or "不明",
            "app_name": self._match_app(snap.foreground_exe) or "不明",
        }

        ordered_rules = sorted(self.rules, key=lambda r: r.get("priority", 0), reverse=True)
        chosen = None
        for rule in ordered_rules:
            if self._rule_matches(rule, snap):
                chosen = rule
                break

        if not chosen:
            chosen = {"name": "fallback", "set": self.fallback}

        set_obj = chosen.get("set", {})
        preset_name = set_obj.get("preset", "")
        preset_data = self.presets.get(preset_name, {})
        presence = self._build_presence(preset_data, set_obj, context)
        return RuleResult(name=chosen.get("name", "unknown"), preset_name=preset_name, presence=presence)

    def _rule_matches(self, rule: Dict[str, Any], snap: Snapshot) -> bool:
        when = rule.get("when", {})
        if "all" in when:
            return all(self._condition_ok(cond, snap) for cond in when["all"])
        if "any" in when:
            return any(self._condition_ok(cond, snap) for cond in when["any"])
        return True

    def _condition_ok(self, cond: Dict[str, Any], snap: Snapshot) -> bool:
        if "foreground_app" in cond:
            return _match_regex(str(cond["foreground_app"]), snap.foreground_exe)
        if "app" in cond or "process" in cond:
            pattern = str(cond.get("app") or cond.get("process"))
            return _match_any(pattern, list(snap.processes))
        if "window_title" in cond:
            return _match_regex(str(cond["window_title"]), snap.window_title)
        if "idle_gte_sec" in cond:
            try:
                return int(snap.idle_sec) >= int(cond["idle_gte_sec"])
            except Exception:
                return False
        if "steam_game" in cond:
            # Check if a Steam game is running
            return bool(cond.get("steam_game")) == snap.is_steam_game
        if "tracked_app" in cond:
            # True when the foreground exe is registered under `apps:`.
            matched = self._match_app(snap.foreground_exe) is not None
            return bool(cond.get("tracked_app")) == matched
        return False

    def _build_presence(
        self,
        preset: Dict[str, Any],
        overrides: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PresenceSpec:
        details = _apply_template(preset.get("details"), context)
        state = _apply_template(preset.get("state"), context)
        assets = preset.get("assets") or {}
        buttons = preset.get("buttons") or []

        cleaned: List[Dict[str, str]] = []
        for btn in buttons[:2]:
            label = str(btn.get("label", ""))[:32]
            url = str(btn.get("url", ""))
            if self.https_only and not url.lower().startswith("https://"):
                continue
            if label and url:
                cleaned.append({"label": label, "url": url})

        return PresenceSpec(
            details=details,
            state=state,
            assets=assets,
            buttons=cleaned,
            elapsed=overrides.get("elapsed"),
        )
