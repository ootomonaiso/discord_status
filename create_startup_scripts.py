"""起動用バッチファイルを生成するスクリプト"""

import sys
from pathlib import Path

def main():
    # パスを取得
    project_root = Path(__file__).parent
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    main_script = project_root / "discord_presence" / "main.py"
    
    # バッチファイルの内容
    batch_content = f"""@echo off
cd /d "{project_root}"
start "" /min "{venv_python}" "{main_script}"
"""
    
    # VBScriptで非表示実行するファイルも作成
    vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{project_root / 'start_discord_presence.bat'}" & chr(34), 0
Set WshShell = Nothing
"""
    
    # バッチファイルを作成
    batch_file = project_root / "start_discord_presence.bat"
    with open(batch_file, "w", encoding="utf-8") as f:
        f.write(batch_content)
    
    # VBScriptファイルを作成
    vbs_file = project_root / "start_discord_presence.vbs"
    with open(vbs_file, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    
    # スタートアップフォルダのパス
    startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    
    print("✓ 起動スクリプトを作成しました:")
    print(f"  - {batch_file}")
    print(f"  - {vbs_file}")
    print()
    print("■ スタートアップに登録する方法:")
    print(f"  1. 以下のファイルをコピー:")
    print(f"     {vbs_file}")
    print(f"  2. 以下のフォルダに貼り付け:")
    print(f"     {startup_folder}")
    print()
    print("  または、以下のコマンドを実行:")
    print(f'  copy "{vbs_file}" "{startup_folder}"')
    print()
    print("■ 手動で起動する方法:")
    print(f"  - コンソールなし: {vbs_file} をダブルクリック")
    print(f"  - コンソールあり: {batch_file} をダブルクリック")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
