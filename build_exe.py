"""Build script to create executable for Discord Rich Presence app."""

import PyInstaller.__main__
import sys
from pathlib import Path

# Get the base directory
base_dir = Path(__file__).parent

# Build the executable
PyInstaller.__main__.run([
    str(base_dir / 'discord_presence' / 'main.py'),
    '--name=DiscordPresence',
    '--onefile',
    '--windowed',
    '--icon=NONE',
    f'--add-data={base_dir / "config.yaml"};.',
    # Make the project root importable so config_editor can be bundled.
    f'--paths={base_dir}',
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--hidden-import=pypresence',
    '--hidden-import=psutil',
    '--hidden-import=win32gui',
    '--hidden-import=win32process',
    '--hidden-import=win32api',
    '--hidden-import=yaml',
    # config_editor doubles as the '--config' GUI entry inside the single exe.
    '--hidden-import=config_editor',
    '--hidden-import=tkinter',
    '--collect-all=pystray',
    '--collect-all=PIL',
    '--noconfirm',
])

print("\n" + "="*60)
print("ビルド完了！")
print(f"実行ファイル: {base_dir / 'dist' / 'DiscordPresence.exe'}")
print("="*60)
