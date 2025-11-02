"""Test the sensor module to verify it's working correctly."""

import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from discord_presence.sensors import take_snapshot

def main():
    print("Testing sensor module...")
    try:
        snapshot = take_snapshot()
        print(f"\n✓ Sensor test successful!")
        print(f"  Foreground app: {snapshot.foreground_exe!r}")
        print(f"  Window title: {snapshot.window_title!r}")
        print(f"  Running processes: {len(snapshot.processes)} detected")
        print(f"  Idle time: {snapshot.idle_sec} seconds")
        print(f"\nSample processes (first 5):")
        for i, proc in enumerate(sorted(snapshot.processes)[:5]):
            print(f"    - {proc}")
    except Exception as e:
        print(f"\n✗ Sensor test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
