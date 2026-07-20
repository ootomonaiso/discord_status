"""Collect ambient state from Windows to drive rule evaluation."""

from __future__ import annotations

import ctypes
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import psutil

logger = logging.getLogger(__name__)
# Prefer pywin32 (win32gui/win32process); if it's not available, provide minimal ctypes-based fallbacks
# so the module can be inspected/used without pywin32 installed.
try:
    import win32gui  # type: ignore
    import win32process  # type: ignore
except Exception:
    # Fallback implementations using ctypes for environments without pywin32.
    class _Win32GuiFallback:
        @staticmethod
        def GetForegroundWindow():
            return ctypes.windll.user32.GetForegroundWindow()

        @staticmethod
        def GetWindowText(hwnd):
            # Use the Unicode API to retrieve the window text
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if not length:
                return ""
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value

    class _Win32ProcessFallback:
        @staticmethod
        def GetWindowThreadProcessId(hwnd):
            pid = ctypes.c_ulong()
            thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return thread_id, pid.value

    win32gui = _Win32GuiFallback()
    win32process = _Win32ProcessFallback()


@dataclass
class Snapshot:
    """Captured state for rule evaluation."""

    foreground_exe: str
    window_title: str
    processes: Set[str]
    idle_sec: int
    is_steam_game: bool = False
    detected_game_name: str = ""


def _get_foreground_info() -> Tuple[str, str]:
    hwnd = win32gui.GetForegroundWindow()
    title = ""
    exe = ""
    try:
        title = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        exe = (proc.name() or "").strip()
    except Exception:
        pass
    return exe, title


def _get_idle_seconds() -> int:
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    liinfo = LASTINPUTINFO()
    liinfo.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(liinfo)):
        return 0
    millis = ctypes.windll.kernel32.GetTickCount() - liinfo.dwTime
    return int(millis / 1000)


def _detect_game_name(exe_name: str, processes: Set[str]) -> str:
    """Detect game name from process list."""
    # Remove .exe extension
    if exe_name.lower().endswith('.exe'):
        game_name = exe_name[:-4]
    else:
        game_name = exe_name
    
    # Clean up common patterns
    game_name = game_name.replace('_', ' ').replace('-', ' ')
    
    # Known game mappings
    game_map = {
        'EldenRing': 'ELDEN RING',
        'sekiro': 'Sekiro',
        'DarkSoulsIII': 'Dark Souls III',
        'DarkSoulsII': 'Dark Souls II',
        'DarkSouls': 'Dark Souls',
        'Overwatch': 'Overwatch',
        'Overwatch2': 'Overwatch 2',
        'VALORANT': 'VALORANT',
        'RiotClient': 'Riot Client',
        'cs2': 'Counter-Strike 2',
        'csgo': 'CS:GO',
        'r5apex': 'Apex Legends',
        'FortniteClient': 'Fortnite',
        'Minecraft': 'Minecraft',
        'LeagueofLegends': 'League of Legends',
        'GenshinImpact': '原神',
        'HonkaiStarRail': '崩壊：スターレイル',
        'RocketLeague': 'Rocket League',
        'FallGuys': 'Fall Guys',
        'DeadByDaylight': 'Dead by Daylight',
        'AmongUs': 'Among Us',
        'PUBG': 'PUBG',
    }
    
    # Check if it's a known game
    for key, value in game_map.items():
        if key.lower() in exe_name.lower():
            return value
    
    # Fallback: capitalize first letter of each word
    return ' '.join(word.capitalize() for word in game_name.split())


# Steam manifests never change once installed, so cache resolved names to avoid
# re-globbing and re-reading every .acf file on each snapshot (~2 times/sec).
_MANIFEST_CACHE: Dict[str, str] = {}


def _read_steam_game_name(library_path: str, folder_name: str) -> str:
    """
    Read the actual game name from Steam's appmanifest files.

    Args:
        library_path: Path to Steam library (e.g., "C:\\Program Files (x86)\\Steam\\steamapps\\common")
        folder_name: Game folder name (e.g., "ELDEN RING")

    Returns:
        Official game name from Steam manifest, or folder name if not found.
    """
    cache_key = f"{library_path}::{folder_name}"
    cached = _MANIFEST_CACHE.get(cache_key)
    if cached is not None:
        return cached

    # The manifest files are in the parent directory (steamapps).
    steamapps_dir = Path(library_path).parent
    resolved = folder_name  # Fallback: the folder name itself.

    try:
        for manifest_file in steamapps_dir.glob("appmanifest_*.acf"):
            try:
                content = manifest_file.read_text(encoding="utf-8", errors="ignore")
                installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)
                name_match = re.search(r'"name"\s+"([^"]+)"', content)
                if (
                    installdir_match
                    and name_match
                    and installdir_match.group(1).lower() == folder_name.lower()
                ):
                    resolved = name_match.group(1)
                    logger.debug("マッチ発見: %s -> %s", folder_name, resolved)
                    break
            except Exception as exc:
                logger.debug("マニフェスト読み取りエラー: %s", exc)
                continue
    except Exception as exc:
        logger.debug("Steamapps検索エラー: %s", exc)

    if resolved == folder_name:
        logger.debug("マニフェストが見つかりません。フォルダ名を使用: %s", folder_name)

    _MANIFEST_CACHE[cache_key] = resolved
    return resolved


# Steam background processes that live inside the library but are not games.
_STEAM_HELPER_MARKERS = (
    "steamwebhelper",
    "steamerrorreporter",
    "steamservice",
    "gameoverlayui",
    "crashhandler",
)


def detect_steam_games(steam_paths: List[str], running_processes: Set[str]) -> Tuple[bool, str]:
    """
    Detect whether a Steam game is running by matching process executables against
    Steam library folders, then resolve the display name from the Steam manifest.

    Returns:
        (is_gaming, game_name): whether a game was detected and its name.
    """
    if not steam_paths:
        return False, ""

    # Map each installed game folder to the library it belongs to.
    game_folders: Dict[Path, str] = {}
    for lib_path in steam_paths:
        lib_dir = Path(lib_path)
        if not lib_dir.exists():
            continue
        try:
            for game_dir in lib_dir.iterdir():
                if game_dir.is_dir():
                    game_folders[game_dir] = lib_path
        except Exception:
            continue

    if not game_folders:
        return False, ""

    # Walk the process table once and check each executable against the folders.
    try:
        processes = list(psutil.process_iter(["name", "exe"]))
    except Exception:
        return False, ""

    for proc in processes:
        try:
            name = (proc.info.get("name") or "").strip()
            if not name or name not in running_processes:
                continue
            if any(marker in name.lower() for marker in _STEAM_HELPER_MARKERS):
                continue

            exe_path = proc.info.get("exe")
            if not exe_path:
                continue
            proc_path = Path(exe_path)

            for game_folder, library_path in game_folders.items():
                if proc_path.parent == game_folder or game_folder in proc_path.parents:
                    game_name = _read_steam_game_name(library_path, game_folder.name)
                    logger.debug("Steamゲーム検出: %s (%s) -> %s", name, proc_path, game_name)
                    return True, game_name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue

    return False, ""


def take_snapshot(steam_paths: Optional[List[str]] = None) -> Snapshot:
    exe, title = _get_foreground_info()
    names: Set[str] = set()
    try:
        for proc in psutil.process_iter(["name"]):
            name = (proc.info.get("name") or "").strip()
            if name:
                names.add(name)
    except Exception:
        pass
    idle = _get_idle_seconds()
    
    # Detect Steam games if paths provided
    is_steam_game = False
    detected_game = ""
    if steam_paths:
        is_steam_game, detected_game = detect_steam_games(steam_paths, names)
    
    return Snapshot(
        foreground_exe=exe,
        window_title=title,
        processes=names,
        idle_sec=idle,
        is_steam_game=is_steam_game,
        detected_game_name=detected_game
    )
