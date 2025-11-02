"""Config editor GUI for Discord Presence."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict

import yaml


class ConfigEditor:
    """GUI for editing config.yaml."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.root = tk.Tk()
        self.root.title("Discord Presence 設定エディタ")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Load config
        self.load_config()

        # Create UI
        self.create_ui()

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込みに失敗しました:\n{e}")
            self.config = {
                "options": {"app_id": "", "restore_last": True, "https_only_buttons": True},
                "timing": {
                    "debounce_ms": 3000,
                    "min_update_sec": 15,
                    "reconnect_backoff": [1, 2, 5, 10, 20],
                },
                "presets": {},
                "rules": [],
                "fallback": {"preset": "idle"},
            }

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with self.config_path.open("w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            messagebox.showinfo("成功", "設定を保存しました")
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました:\n{e}")

    def create_ui(self) -> None:
        """Create the main UI."""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Basic settings
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本設定")
        self.create_basic_tab(basic_frame)

        # Tab 2: Presets
        presets_frame = ttk.Frame(notebook)
        notebook.add(presets_frame, text="プリセット")
        self.create_presets_tab(presets_frame)

        # Tab 3: Rules
        rules_frame = ttk.Frame(notebook)
        notebook.add(rules_frame, text="ルール")
        self.create_rules_tab(rules_frame)

        # Tab 4: Timing
        timing_frame = ttk.Frame(notebook)
        notebook.add(timing_frame, text="タイミング")
        self.create_timing_tab(timing_frame)

        # Bottom buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="保存", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=self.root.quit).pack(side=tk.RIGHT)

    def create_basic_tab(self, parent: ttk.Frame) -> None:
        """Create basic settings tab."""
        options = self.config.get("options", {})

        # Application ID
        ttk.Label(parent, text="Discord Application ID:", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))
        app_id_var = tk.StringVar(value=options.get("app_id", ""))
        app_id_entry = ttk.Entry(parent, textvariable=app_id_var, width=50)
        app_id_entry.pack(anchor=tk.W, padx=10, pady=5)

        ttk.Label(
            parent,
            text="取得方法: https://discord.com/developers/applications で新規アプリを作成し、\nApplication IDをコピーしてください。",
            foreground="gray",
        ).pack(anchor=tk.W, padx=10, pady=5)

        # AFK threshold
        ttk.Label(parent, text="寝落ち検出時間 (秒):", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(20, 5))
        afk_var = tk.IntVar(value=options.get("afk_idle_sec", 1800))
        afk_spin = ttk.Spinbox(parent, from_=300, to=7200, textvariable=afk_var, width=20)
        afk_spin.pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(
            parent,
            text="この時間以上マウス・キーボード操作がないと「寝落ち」と表示されます (デフォルト: 1800秒 = 30分)",
            foreground="gray",
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Checkboxes
        restore_var = tk.BooleanVar(value=options.get("restore_last", True))
        ttk.Checkbutton(parent, text="起動時に前回の状態を復元", variable=restore_var).pack(anchor=tk.W, padx=10, pady=10)

        https_var = tk.BooleanVar(value=options.get("https_only_buttons", True))
        ttk.Checkbutton(parent, text="ボタンURLをHTTPSのみに制限", variable=https_var).pack(anchor=tk.W, padx=10, pady=5)

        # Save to config
        def update_options():
            self.config.setdefault("options", {})
            self.config["options"]["app_id"] = app_id_var.get()
            self.config["options"]["restore_last"] = restore_var.get()
            self.config["options"]["https_only_buttons"] = https_var.get()
            self.config["options"]["afk_idle_sec"] = afk_var.get()

        self.root.protocol("WM_DELETE_WINDOW", lambda: (update_options(), self.root.quit()))

        # Store update function
        self._update_basic = update_options

    def create_presets_tab(self, parent: ttk.Frame) -> None:
        """Create presets tab."""
        presets = self.config.get("presets", {})

        # List frame
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        ttk.Label(list_frame, text="プリセット一覧:", font=("", 10, "bold")).pack(anchor=tk.W, pady=5)

        preset_listbox = tk.Listbox(list_frame, width=30, height=20)
        preset_listbox.pack(fill=tk.BOTH, expand=True)

        for preset_name in presets.keys():
            preset_listbox.insert(tk.END, preset_name)

        # Edit frame
        edit_frame = ttk.Frame(parent)
        edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(edit_frame, text="プリセット編集:", font=("", 10, "bold")).pack(anchor=tk.W, pady=5)

        # Name
        ttk.Label(edit_frame, text="名前:").pack(anchor=tk.W, pady=(10, 0))
        name_var = tk.StringVar()
        name_entry = ttk.Entry(edit_frame, textvariable=name_var, width=40)
        name_entry.pack(anchor=tk.W, pady=5)

        # Details
        ttk.Label(edit_frame, text="Details (上段テキスト):").pack(anchor=tk.W, pady=(10, 0))
        details_var = tk.StringVar()
        details_entry = ttk.Entry(edit_frame, textvariable=details_var, width=40)
        details_entry.pack(anchor=tk.W, pady=5)
        ttk.Label(edit_frame, text="変数: {workspace}, {window_title}, {foreground_exe}", foreground="gray").pack(
            anchor=tk.W, padx=10
        )

        # State
        ttk.Label(edit_frame, text="State (下段テキスト):").pack(anchor=tk.W, pady=(10, 0))
        state_var = tk.StringVar()
        state_entry = ttk.Entry(edit_frame, textvariable=state_var, width=40)
        state_entry.pack(anchor=tk.W, pady=5)

        # Large image
        ttk.Label(edit_frame, text="Large Image (アセットキー):").pack(anchor=tk.W, pady=(10, 0))
        large_img_var = tk.StringVar()
        large_img_entry = ttk.Entry(edit_frame, textvariable=large_img_var, width=40)
        large_img_entry.pack(anchor=tk.W, pady=5)

        # Small image
        ttk.Label(edit_frame, text="Small Image (アセットキー):").pack(anchor=tk.W, pady=(10, 0))
        small_img_var = tk.StringVar()
        small_img_entry = ttk.Entry(edit_frame, textvariable=small_img_var, width=40)
        small_img_entry.pack(anchor=tk.W, pady=5)

        # Buttons
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(anchor=tk.W, pady=10)

        def load_preset():
            selection = preset_listbox.curselection()
            if not selection:
                return
            preset_name = preset_listbox.get(selection[0])
            preset = presets.get(preset_name, {})
            name_var.set(preset_name)
            details_var.set(preset.get("details", ""))
            state_var.set(preset.get("state", ""))
            assets = preset.get("assets", {})
            large_img_var.set(assets.get("large_image", ""))
            small_img_var.set(assets.get("small_image", ""))

        def save_preset():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("エラー", "プリセット名を入力してください")
                return

            preset = {
                "details": details_var.get(),
                "state": state_var.get(),
                "assets": {},
            }
            if large_img_var.get():
                preset["assets"]["large_image"] = large_img_var.get()
            if small_img_var.get():
                preset["assets"]["small_image"] = small_img_var.get()

            self.config.setdefault("presets", {})
            self.config["presets"][name] = preset

            # Update listbox
            if name not in preset_listbox.get(0, tk.END):
                preset_listbox.insert(tk.END, name)

            messagebox.showinfo("成功", f"プリセット '{name}' を保存しました")

        def delete_preset():
            selection = preset_listbox.curselection()
            if not selection:
                messagebox.showerror("エラー", "削除するプリセットを選択してください")
                return
            preset_name = preset_listbox.get(selection[0])
            if messagebox.askyesno("確認", f"プリセット '{preset_name}' を削除しますか?"):
                del self.config["presets"][preset_name]
                preset_listbox.delete(selection[0])
                # Clear fields
                name_var.set("")
                details_var.set("")
                state_var.set("")
                large_img_var.set("")
                small_img_var.set("")

        def new_preset():
            name_var.set("")
            details_var.set("")
            state_var.set("")
            large_img_var.set("")
            small_img_var.set("")

        preset_listbox.bind("<<ListboxSelect>>", lambda e: load_preset())

        ttk.Button(button_frame, text="新規", command=new_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存", command=save_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="削除", command=delete_preset).pack(side=tk.LEFT, padx=5)

    def create_rules_tab(self, parent: ttk.Frame) -> None:
        """Create rules tab."""
        rules = self.config.get("rules", [])

        # Simple text view for now
        ttk.Label(parent, text="ルール設定 (YAML直接編集):", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=10)

        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        rules_text = tk.Text(text_frame, yscrollcommand=scrollbar.set, width=80, height=20)
        rules_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=rules_text.yview)

        # Populate text
        rules_text.insert("1.0", yaml.dump({"rules": rules}, allow_unicode=True, default_flow_style=False))

        def save_rules():
            try:
                content = rules_text.get("1.0", tk.END)
                parsed = yaml.safe_load(content)
                self.config["rules"] = parsed.get("rules", [])
                messagebox.showinfo("成功", "ルールを保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"YAML解析エラー:\n{e}")

        ttk.Button(parent, text="ルールを保存", command=save_rules).pack(pady=10)

    def create_timing_tab(self, parent: ttk.Frame) -> None:
        """Create timing settings tab."""
        timing = self.config.get("timing", {})

        ttk.Label(parent, text="タイミング設定:", font=("", 10, "bold")).pack(anchor=tk.W, padx=10, pady=10)

        # Debounce
        ttk.Label(parent, text="デバウンス時間 (ミリ秒):").pack(anchor=tk.W, padx=10, pady=(10, 0))
        debounce_var = tk.IntVar(value=timing.get("debounce_ms", 3000))
        debounce_spin = ttk.Spinbox(parent, from_=0, to=10000, textvariable=debounce_var, width=20)
        debounce_spin.pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(parent, text="ルールが安定してから適用するまでの待機時間", foreground="gray").pack(anchor=tk.W, padx=20)

        # Min update
        ttk.Label(parent, text="最小更新間隔 (秒):").pack(anchor=tk.W, padx=10, pady=(10, 0))
        min_update_var = tk.IntVar(value=timing.get("min_update_sec", 15))
        min_update_spin = ttk.Spinbox(parent, from_=1, to=300, textvariable=min_update_var, width=20)
        min_update_spin.pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(parent, text="連続更新を防ぐための最小間隔", foreground="gray").pack(anchor=tk.W, padx=20)

        def update_timing():
            self.config.setdefault("timing", {})
            self.config["timing"]["debounce_ms"] = debounce_var.get()
            self.config["timing"]["min_update_sec"] = min_update_var.get()

        self._update_timing = update_timing

    def run(self) -> None:
        """Run the GUI."""
        self.root.mainloop()

        # Update all sections before closing
        if hasattr(self, "_update_basic"):
            self._update_basic()
        if hasattr(self, "_update_timing"):
            self._update_timing()


def main():
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        if not messagebox.askyesno(
            "確認", f"設定ファイルが見つかりません:\n{config_path}\n\n新規作成しますか?"
        ):
            sys.exit(0)

    editor = ConfigEditor(config_path)
    editor.run()


if __name__ == "__main__":
    main()
