"""Test the rule engine with a mock snapshot."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from discord_presence.rules import RuleEngine
from discord_presence.sensors import Snapshot
import yaml

def main():
    print("Testing rule engine...")
    
    # Load config
    cfg_path = Path(__file__).parent / "config.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    engine = RuleEngine(cfg)
    
    # Test 1: VS Code window
    print("\n--- Test 1: VS Code foreground ---")
    snap1 = Snapshot(
        foreground_exe="Code.exe",
        window_title="discord - Visual Studio Code",
        processes={"Code.exe", "chrome.exe", "explorer.exe"},
        idle_sec=0
    )
    result1 = engine.evaluate(snap1)
    print(f"  Rule: {result1.name}")
    print(f"  Preset: {result1.preset_name}")
    print(f"  Details: {result1.presence.details!r}")
    print(f"  State: {result1.presence.state!r}")
    
    # Test 2: Meeting app
    print("\n--- Test 2: Zoom meeting ---")
    snap2 = Snapshot(
        foreground_exe="Zoom.exe",
        window_title="Zoom Meeting",
        processes={"Zoom.exe", "chrome.exe"},
        idle_sec=0
    )
    result2 = engine.evaluate(snap2)
    print(f"  Rule: {result2.name}")
    print(f"  Preset: {result2.preset_name}")
    print(f"  Details: {result2.presence.details!r}")
    print(f"  State: {result2.presence.state!r}")
    
    # Test 3: Browser active
    print("\n--- Test 3: Chrome browsing (active) ---")
    snap3 = Snapshot(
        foreground_exe="chrome.exe",
        window_title="YouTube - Google Chrome",
        processes={"chrome.exe"},
        idle_sec=10
    )
    result3 = engine.evaluate(snap3)
    print(f"  Rule: {result3.name}")
    print(f"  Preset: {result3.preset_name}")
    print(f"  Details: {result3.presence.details!r}")
    print(f"  State: {result3.presence.state!r}")
    
    # Test 3b: Browser idle
    print("\n--- Test 3b: Browser with 150 seconds idle ---")
    snap3b = Snapshot(
        foreground_exe="chrome.exe",
        window_title="YouTube - Google Chrome",
        processes={"chrome.exe"},
        idle_sec=150
    )
    result3b = engine.evaluate(snap3b)
    print(f"  Rule: {result3b.name}")
    print(f"  Preset: {result3b.preset_name}")
    print(f"  Details: {result3b.presence.details!r}")
    print(f"  State: {result3b.presence.state!r}")
    
    # Test 4: Gaming detection
    print("\n--- Test 4: Gaming (Elden Ring) ---")
    snap4 = Snapshot(
        foreground_exe="EldenRing.exe",
        window_title="ELDEN RING",
        processes={"EldenRing.exe", "steam.exe"},
        idle_sec=0
    )
    result4 = engine.evaluate(snap4)
    print(f"  Rule: {result4.name}")
    print(f"  Preset: {result4.preset_name}")
    print(f"  Details: {result4.presence.details!r}")
    print(f"  State: {result4.presence.state!r}")
    
    # Test 5: Fallback
    print("\n--- Test 5: Unknown app (fallback) ---")
    snap5 = Snapshot(
        foreground_exe="notepad.exe",
        window_title="Untitled - Notepad",
        processes={"notepad.exe"},
        idle_sec=0
    )
    result5 = engine.evaluate(snap5)
    print(f"  Rule: {result5.name}")
    print(f"  Preset: {result5.preset_name}")
    print(f"  Details: {result5.presence.details!r}")
    print(f"  State: {result5.presence.state!r}")
    
    print("\n✓ All rule engine tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
