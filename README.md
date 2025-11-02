# Discord Rich Presence Manager# Discord Rich Presence 常駐アプリ



Windowsの常駐アプリケーションとして動作し、現在の作業状況に応じてDiscordのリッチプレゼンスを自動更新するツールです。Windowsのタスクトレイに常駐し、起動中のアプリやアイドル時間に応じてDiscordのRich Presenceを自動更新するツールです。



## ✨ 特徴## 特徴

- 🖥️ **タスクトレイ常駐**: バックグラウンドで動作し、トレイアイコンから操作可能

### 🎮 自動ゲーム検出- 🔄 **自動切替**: VS Code、会議アプリ、ブラウザなどを検出して自動的にステータス変更

- **Steamライブラリスキャン**: Steamのマニフェストファイルから正式なゲーム名を自動取得- 🎮 **手動切替**: トレイメニューからワンクリックでプリセット選択

- **プロセス名マッチング**: 主要なゲームを自動認識（ELDEN RING、Apex Legends、VALORANTなど）- 🇯🇵 **日本語対応**: メニューとメッセージは全て日本語

- **誤検出防止**: ゲームディレクトリとプロセスパスの照合で高精度な検出- ⚙️ **カスタマイズ可能**: `config.yaml`で自由にルールとプリセットを設定



### 💼 開発環境の自動検出## セットアップ

- VS Codeでの作業を検出（ワークスペース名を表示）

- ブラウジング中かアイドル状態かを判別### 1. Python環境の準備

- Zoom/Teamsなどの会議アプリを検出```powershell

cd "c:\Users\ootom\OneDrive\デスクトップ\discord"

### 🎯 ステータスとアクティビティの独立制御py -3.11 -m venv .venv

- **ステータス**: 参加OK / 忙しい / ひとりで（手動切替）.\.venv\Scripts\Activate.ps1

- **アクティビティ**: ゲーム中 / 開発中 / 会議中など（自動検出または手動選択）pip install -r requirements.txt

- 例: ゲーム中でも「参加OK」ステータスに設定可能```



### 😴 AFK検出### 2. 設定エディタで初期設定

- 30分以上の無操作で「寝落ち」表示（設定変更可能）```powershell

python .\config_editor.py

### 🎨 GUIエディタ```

- `config_editor.py` で設定を簡単に編集

- プリセット、ルール、タイミングをGUIで管理設定エディタのGUIで以下を設定：



## 📋 必要要件#### 基本設定タブ

1. **Discord Application ID** の取得：

- **OS**: Windows 10/11   - https://discord.com/developers/applications にアクセス

- **Python**: 3.10以上（開発時は3.13.7で動作確認）   - "New Application" で新規アプリを作成

- **Discord**: デスクトップアプリ   - "Application ID" をコピーして貼り付け



## 🚀 セットアップ#### プリセットタブ

- デフォルトのプリセットを編集、または新規作成

### 1. Discord Developer Portalでアプリケーションを作成- `details` (上段)、`state` (下段)、画像アセットキーを設定

- 変数 `{workspace}`, `{window_title}` などが使用可能

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス

2. 「New Application」をクリックしてアプリケーションを作成#### ルールタブ

3. 「Rich Presence」→「Art Assets」でアイコン画像をアップロード- 自動切替のルールをYAML形式で編集

   - 推奨サイズ: 512x512px以上- 優先度、条件（アプリ名、プロセス名、アイドル時間）を設定

   - アセット名例: `status`, `ok`, `busy`, `solo`, `code`, `game`, `meeting`, `coffee`, `browser`, `idle`, `sleep`, `afk`

4. 「General Information」からアプリケーションIDをコピー#### タイミングタブ

- デバウンス時間、最小更新間隔を調整

### 2. リポジトリをクローン

**保存ボタンで設定を保存**

```bash

git clone https://github.com/YOUR_USERNAME/discord-presence-manager.git### 3. （オプション）アセット画像の登録

cd discord-presence-managerDeveloper Portal の "Rich Presence" → "Art Assets" で以下のキー名で画像をアップロード：

```- `code` - VS Code用

- `meeting` - 会議用

### 3. 仮想環境を作成して依存関係をインストール- `coffee` - 休憩用

- `game` - ゲーム用

```bash

python -m venv .venvまたは、`config.yaml` を直接編集することも可能です。

.\.venv\Scripts\activate

pip install -r requirements.txt## 起動方法

```

### 手動起動

### 4. 設定ファイルを作成```powershell

# コンソール表示あり

```bashpython .\discord_presence\main.py

# サンプルファイルをコピー

copy config.yaml.example config.yaml# コンソールなし（バックグラウンド）

.\start_discord_presence.vbs

# config.yamlを編集```

notepad config.yaml

```### スタートアップ登録（自動起動）

```powershell

`config.yaml` の `app_id` にDiscordアプリケーションIDを設定：# 起動スクリプトを生成

python .\create_startup_scripts.py

```yaml

options:# スタートアップフォルダにコピー

  app_id: "YOUR_DISCORD_APP_ID"  # ← ここに設定copy "start_discord_presence.vbs" "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"

``````



Steamライブラリパスも必要に応じて設定：## 使い方



```yaml### トレイアイコンメニュー

  steam_library_paths:- **現在**: 現在適用中のプリセット名

    - "C:\\Program Files (x86)\\Steam\\steamapps\\common"- **ルール**: 適用中のルール名（自動モード時）

    - "D:\\SteamLibrary\\steamapps\\common"  # 追加ライブラリがあれば- **自動切替**: オン/オフ切替（チェック付きで有効）

```- **ステータス**: 手動でステータスを切り替え

  - ✅ **参加OK** - いつでも声かけてね

### 5. 起動  - 🚫 **忙しい** - 集中中、参加NG

  - 🎧 **ひとりで作業中** - ソロタイム、参加NG

#### Pythonスクリプトから起動- **プリセット**: アプリ別プリセットを選択

  - 作業中 (VS Code)

```bash  - 会議中

python discord_presence\main.py  - 休憩中

```  - ゲーム中

  - 待機中

#### EXEファイルをビルドして起動- **設定を開く**: 設定エディタGUIを起動

- **終了**: アプリを終了してPresenceをクリア

```bash

# ビルド### 設定エディタ

python build_exe.pyタスクトレイから「設定を開く」を選択するか、直接起動：

```powershell

# config.yamlをdistフォルダにコピーpython .\config_editor.py

copy config.yaml dist\```



# 実行GUIで簡単に設定を編集・保存できます：

dist\DiscordPresence.exe- **基本設定**: Application ID、寝落ち検出時間、その他オプション

```- **プリセット**: 新規作成、編集、削除

- **ルール**: YAML形式で編集

## 📖 使い方- **タイミング**: デバウンス、更新間隔



### タスクトレイアイコン### 寝落ち検出の設定

設定エディタの「基本設定」タブで変更可能：

起動すると、タスクトレイにアイコンが表示されます。右クリックでメニューを開きます：- デフォルト: 1800秒（30分）

- 推奨範囲: 900秒（15分）〜 3600秒（1時間）

- **現在の状態**: 現在適用中のルールとプリセットを表示- 自動モード時のみ動作（手動ステータス選択時は無効）

- **自動切替**: 自動検出のON/OFF

- **ステータス**: ### 自動切替のルール（デフォルト）

  - 🔄 自動（ルールに従う）1. **寝落ち検出** (優先度: 95) 😴

  - ✅ 参加OK   - 30分以上マウス・キーボード操作なし

  - 🚫 忙しい   - 「寝落ち...? 反応ないかも」と表示

  - 🎧 ひとりで   - 設定で時間変更可能（例: 15分、1時間など）

- **アクティビティ**:2. **会議中** (優先度: 90) 📞

  - 🔄 自動検出   - Zoom、Teamsが起動中

  - 💻 作業中 (VS Code)3. **開発中** (優先度: 70) 💻

  - 📞 会議中   - VS Codeが前面ウィンドウ

  - ☕ 休憩中   - ワークスペース名を自動表示

  - 🎮 ゲーム中4. **ゲーム中** (優先度: 65) 🎮

  - ⏸️ 待機中   - Steam/Epic/その他ゲームランチャーから起動したゲームを検出

- **設定を開く**: GUIエディタを起動   - ゲーム名を自動表示（例: "ゲーム中: ELDEN RING"）

- **終了**: アプリケーションを終了   - 対応ゲーム: ELDEN RING, Sekiro, Overwatch, VALORANT, Apex Legends, CS2, Fortnite, Minecraft など

5. **ブラウザアイドル** (優先度: 55) ☕

### 設定エディタ   - ブラウザが前面 & 2分以上アイドル → 「ぶらっと隙間時間」

6. **ネットサーフィン** (優先度: 50) 🌐

```bash   - Chrome/Edge/Firefoxが前面 & アクティブ操作中

python config_editor.py7. **待機中** (フォールバック) 💤

```   - 上記に該当しない場合



4つのタブで設定を管理：## カスタマイズ



1. **基本設定**: アプリケーションID、AFK時間、Steamパス### プリセットの追加

2. **プリセット**: 各状態の表示内容を編集`config.yaml` の `presets` セクション：

3. **ルール**: 自動切替の条件を設定```yaml

4. **タイミング**: デバウンス、更新間隔、再接続設定presets:

  my_preset:

## ⚙️ 設定ファイルの詳細    details: "カスタムステータス"

    state: "参加OK"

### プリセット    assets: { large_image: "my_icon" }

```

各プリセットで表示内容を定義：

### ルールの追加

```yaml`config.yaml` の `rules` セクション：

presets:```yaml

  gaming:rules:

    details: "ゲーム中: {game_name}"  # {game_name}は自動置換  - name: my rule

    state: "参加NG"    priority: 75

    assets:    when:

      large_image: "game"  # Discord Developer Portalでアップロードしたアセット名      any:

      small_image: "busy"        - foreground_app: "myapp.exe"

```    set: { preset: "my_preset" }

```

### ルール

### 条件の種類

優先度順に評価され、最初にマッチしたルールを適用：- `foreground_app`: 前面ウィンドウのexe名（正規表現）

- `app` / `process`: 起動中のプロセス名（正規表現）

```yaml- `window_title`: ウィンドウタイトル（正規表現）

rules:- `idle_gte_sec`: アイドル時間（秒）以上

  - name: steam library game

    priority: 68  # 数値が大きいほど優先## トラブルシューティング

    when:

      all:  # すべての条件を満たす場合### Discord RPC に接続できない

        - steam_game: true- Discordクライアントが起動しているか確認

    set:- Application IDが正しいか確認

      preset: "gaming"- ファイアウォール設定を確認

```

### ルールが適用されない

#### 利用可能な条件```powershell

# センサーの動作確認

- `foreground_app`: 前面ウィンドウのプロセス名（正規表現）python .\test_sensors.py

- `process`: 実行中のプロセス名（正規表現）

- `idle_gte_sec`: アイドル時間（秒）以上# ルールエンジンのテスト

- `steam_game`: Steamゲーム検出（true/false）python .\test_rules.py

```

### タイミング設定

### タスクトレイアイコンが表示されない

```yaml- pystrayとPillowがインストールされているか確認

timing:- コンソールにエラーメッセージが表示されていないか確認

  debounce_ms: 3000        # 状態が安定してから更新するまでの時間（ミリ秒）

  min_update_sec: 15       # 最小更新間隔（秒）## 注意事項

  reconnect_backoff: [1, 2, 5, 10, 20]  # 再接続時の待機時間（秒）- Discord Rich Presence RPCのみ使用（規約準拠）

```- カスタムステータス（絵文字付き）の変更は非対応

- 表示は実行中のPCでのみ有効

## 🔧 カスタマイズ

### ゲームの追加

`config.yaml` の `rules` セクションに追加：

```yaml
rules:
  - name: my custom game
    priority: 65
    when:
      any:
        - process: "MyGame\\.exe"
    set:
      preset: "gaming"
```

### 新しいプリセットの作成

```yaml
presets:
  my_custom_status:
    details: "カスタム状態"
    state: "自由に設定"
    assets:
      large_image: "custom_icon"
```

### ルールの変更

優先度（priority）の数値を変更することで、適用順序を制御できます。
数値が大きいほど優先されます。

## 🐛 トラブルシューティング

### Discord Developer Portalのエラー

**Q: "Invalid Asset" エラーが出る**  
A: `config.yaml` の `assets` セクションで指定している画像名が、Discord Developer Portalにアップロードされているか確認してください。

### ゲーム検出されない

**Q: Steamゲームが検出されない**  
A: `config.yaml` の `steam_library_paths` にゲームがインストールされているパスが含まれているか確認してください。

```yaml
steam_library_paths:
  - "C:\\Program Files (x86)\\Steam\\steamapps\\common"
  - "D:\\SteamLibrary\\steamapps\\common"  # ← 追加ライブラリ
```

**Q: 特定のゲームが検出されない**  
A: ゲームのプロセス名を確認し、`rules` に追加してください：

```yaml
rules:
  - name: my game
    priority: 65
    when:
      any:
        - process: "GameProcess\\.exe"  # ← ゲームのプロセス名
    set:
      preset: "gaming"
```

### 起動しない

**Q: "config.yaml が見つかりません" エラー**  
A: `config.yaml` が実行ファイルと同じディレクトリにあるか確認してください。

**Q: "options.app_id を設定してください" エラー**  
A: `config.yaml` の `app_id` にDiscordアプリケーションIDを設定してください。

## 📝 ファイル構成

```
discord-presence-manager/
├── discord_presence/
│   ├── __init__.py
│   ├── main.py           # エントリーポイント
│   ├── rpc_client.py     # Discord RPC クライアント
│   ├── sensors.py        # システム状態検出
│   ├── rules.py          # ルールエンジン
│   └── tray.py           # トレイアイコン
├── config_editor.py      # GUI設定エディタ
├── build_exe.py          # EXEビルドスクリプト
├── config.yaml.example   # 設定ファイルのサンプル
├── requirements.txt      # 依存パッケージ
├── .gitignore
└── README.md
```

## 🛠️ 開発

### テスト

```bash
# ルールエンジンのテスト
python test_rules.py

# センサーのテスト
python test_sensors.py
```

### スタートアップスクリプトの生成

Windows起動時に自動実行するスクリプトを生成：

```bash
python create_startup_scripts.py
```

生成されたファイル：
- `start_discord_presence.bat`: コンソール表示あり
- `start_discord_presence.vbs`: バックグラウンド実行

スタートアップフォルダに配置：
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

## 📦 依存パッケージ

- `pypresence==4.6.1`: Discord Rich Presence API
- `psutil==7.1.2`: プロセス・システム情報取得
- `pywin32==311`: Windows API
- `PyYAML==6.0.3`: YAML設定ファイル
- `pystray==0.19.5`: システムトレイアイコン
- `Pillow==12.0.0`: アイコン画像生成

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

プルリクエスト歓迎です！

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 🙏 謝辞

- [pypresence](https://github.com/qwertyquerty/pypresence) - Discord RPC ライブラリ
- [pystray](https://github.com/moses-palmer/pystray) - システムトレイアイコンライブラリ

## 📮 サポート

Issue を作成してください
