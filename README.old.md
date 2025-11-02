# Discord Rich Presence 常駐アプリ

Windowsのタスクトレイに常駐し、起動中のアプリやアイドル時間に応じてDiscordのRich Presenceを自動更新するツールです。

## 特徴
- 🖥️ **タスクトレイ常駐**: バックグラウンドで動作し、トレイアイコンから操作可能
- 🔄 **自動切替**: VS Code、会議アプリ、ブラウザなどを検出して自動的にステータス変更
- 🎮 **手動切替**: トレイメニューからワンクリックでプリセット選択
- 🇯🇵 **日本語対応**: メニューとメッセージは全て日本語
- ⚙️ **カスタマイズ可能**: `config.yaml`で自由にルールとプリセットを設定

## セットアップ

### 1. Python環境の準備
```powershell
cd "c:\Users\ootom\OneDrive\デスクトップ\discord"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 設定エディタで初期設定
```powershell
python .\config_editor.py
```

設定エディタのGUIで以下を設定：

#### 基本設定タブ
1. **Discord Application ID** の取得：
   - https://discord.com/developers/applications にアクセス
   - "New Application" で新規アプリを作成
   - "Application ID" をコピーして貼り付け

#### プリセットタブ
- デフォルトのプリセットを編集、または新規作成
- `details` (上段)、`state` (下段)、画像アセットキーを設定
- 変数 `{workspace}`, `{window_title}` などが使用可能

#### ルールタブ
- 自動切替のルールをYAML形式で編集
- 優先度、条件（アプリ名、プロセス名、アイドル時間）を設定

#### タイミングタブ
- デバウンス時間、最小更新間隔を調整

**保存ボタンで設定を保存**

### 3. （オプション）アセット画像の登録
Developer Portal の "Rich Presence" → "Art Assets" で以下のキー名で画像をアップロード：
- `code` - VS Code用
- `meeting` - 会議用
- `coffee` - 休憩用
- `game` - ゲーム用

または、`config.yaml` を直接編集することも可能です。

## 起動方法

### 手動起動
```powershell
# コンソール表示あり
python .\discord_presence\main.py

# コンソールなし（バックグラウンド）
.\start_discord_presence.vbs
```

### スタートアップ登録（自動起動）
```powershell
# 起動スクリプトを生成
python .\create_startup_scripts.py

# スタートアップフォルダにコピー
copy "start_discord_presence.vbs" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
```

## 使い方

### トレイアイコンメニュー
- **現在**: 現在適用中のプリセット名
- **ルール**: 適用中のルール名（自動モード時）
- **自動切替**: オン/オフ切替（チェック付きで有効）
- **ステータス**: 手動でステータスを切り替え
  - ✅ **参加OK** - いつでも声かけてね
  - 🚫 **忙しい** - 集中中、参加NG
  - 🎧 **ひとりで作業中** - ソロタイム、参加NG
- **プリセット**: アプリ別プリセットを選択
  - 作業中 (VS Code)
  - 会議中
  - 休憩中
  - ゲーム中
  - 待機中
- **設定を開く**: 設定エディタGUIを起動
- **終了**: アプリを終了してPresenceをクリア

### 設定エディタ
タスクトレイから「設定を開く」を選択するか、直接起動：
```powershell
python .\config_editor.py
```

GUIで簡単に設定を編集・保存できます：
- **基本設定**: Application ID、寝落ち検出時間、その他オプション
- **プリセット**: 新規作成、編集、削除
- **ルール**: YAML形式で編集
- **タイミング**: デバウンス、更新間隔

### 寝落ち検出の設定
設定エディタの「基本設定」タブで変更可能：
- デフォルト: 1800秒（30分）
- 推奨範囲: 900秒（15分）〜 3600秒（1時間）
- 自動モード時のみ動作（手動ステータス選択時は無効）

### 自動切替のルール（デフォルト）
1. **寝落ち検出** (優先度: 95) 😴
   - 30分以上マウス・キーボード操作なし
   - 「寝落ち...? 反応ないかも」と表示
   - 設定で時間変更可能（例: 15分、1時間など）
2. **会議中** (優先度: 90) 📞
   - Zoom、Teamsが起動中
3. **開発中** (優先度: 70) 💻
   - VS Codeが前面ウィンドウ
   - ワークスペース名を自動表示
4. **ゲーム中** (優先度: 65) 🎮
   - Steam/Epic/その他ゲームランチャーから起動したゲームを検出
   - ゲーム名を自動表示（例: "ゲーム中: ELDEN RING"）
   - 対応ゲーム: ELDEN RING, Sekiro, Overwatch, VALORANT, Apex Legends, CS2, Fortnite, Minecraft など
5. **ブラウザアイドル** (優先度: 55) ☕
   - ブラウザが前面 & 2分以上アイドル → 「ぶらっと隙間時間」
6. **ネットサーフィン** (優先度: 50) 🌐
   - Chrome/Edge/Firefoxが前面 & アクティブ操作中
7. **待機中** (フォールバック) 💤
   - 上記に該当しない場合

## カスタマイズ

### プリセットの追加
`config.yaml` の `presets` セクション：
```yaml
presets:
  my_preset:
    details: "カスタムステータス"
    state: "参加OK"
    assets: { large_image: "my_icon" }
```

### ルールの追加
`config.yaml` の `rules` セクション：
```yaml
rules:
  - name: my rule
    priority: 75
    when:
      any:
        - foreground_app: "myapp.exe"
    set: { preset: "my_preset" }
```

### 条件の種類
- `foreground_app`: 前面ウィンドウのexe名（正規表現）
- `app` / `process`: 起動中のプロセス名（正規表現）
- `window_title`: ウィンドウタイトル（正規表現）
- `idle_gte_sec`: アイドル時間（秒）以上

## トラブルシューティング

### Discord RPC に接続できない
- Discordクライアントが起動しているか確認
- Application IDが正しいか確認
- ファイアウォール設定を確認

### ルールが適用されない
```powershell
# センサーの動作確認
python .\test_sensors.py

# ルールエンジンのテスト
python .\test_rules.py
```

### タスクトレイアイコンが表示されない
- pystrayとPillowがインストールされているか確認
- コンソールにエラーメッセージが表示されていないか確認

## 注意事項
- Discord Rich Presence RPCのみ使用（規約準拠）
- カスタムステータス（絵文字付き）の変更は非対応
- 表示は実行中のPCでのみ有効
