# Discord Rich Presence Manager - Copilot Instructions

このプロジェクトは、Windowsで動作するDiscord Rich Presence自動更新ツールです。

## プロジェクト概要

- **言語**: Python 3.13
- **アーキテクチャ**: イベント駆動型常駐アプリケーション
- **主要機能**: 
  - システム状態検出（前面アプリ、プロセス、アイドル時間、Steamゲーム）
  - ルールベースの自動切替
  - 手動ステータス/アクティビティ切替
  - システムトレイUI

## config.yaml編集時のガイドライン

### 基本構造

```yaml
options:       # アプリケーション設定
presets:       # 表示内容のテンプレート
rules:         # 自動切替ルール（優先度順）
fallback:      # デフォルト状態
timing:        # タイミング制御
```

### プリセットの追加

新しいプリセットを追加する際は、以下の形式を使用：

```yaml
presets:
  preset_name:
    details: "メイン表示テキスト"  # 必須
    state: "サブ表示テキスト"      # オプション
    assets:                         # オプション
      large_image: "asset_name"     # Discord Developer Portalにアップロード済みの画像名
      small_image: "asset_name"     # 同上
    buttons:                        # オプション（最大2個）
      - label: "ボタンテキスト"
        url: "https://example.com"
```

**テンプレート変数**（自動置換）:
- `{game_name}` - 検出されたゲーム名
- `{workspace}` - VS Codeのワークスペース名
- `{window_title}` - 前面ウィンドウのタイトル
- `{foreground_exe}` - 前面アプリのプロセス名
- `{idle_sec}` - アイドル時間（秒）

### ルールの追加

優先度の高い順（大きい数値）から評価されます：

```yaml
rules:
  - name: rule_name                 # ルール名（ログ用）
    priority: 70                    # 数値が大きいほど優先（0-100推奨）
    when:                           # 条件
      all:                          # すべて満たす（AND条件）
        - condition: value
      # または
      any:                          # いずれか満たす（OR条件）
        - condition: value
    set:                            # 適用する内容
      preset: "preset_name"         # プリセット名
      elapsed: start                # オプション: 経過時間表示（start/none）
```

**利用可能な条件**:
- `foreground_app: "regex"` - 前面アプリのプロセス名（正規表現）
- `process: "regex"` - 実行中のプロセス名（正規表現）
- `idle_gte_sec: 数値` - アイドル時間が指定秒数以上
- `steam_game: true` - Steamゲーム検出（true/false）

**正規表現の例**:
- `"Code\\.exe"` - Code.exeに完全一致
- `"Code.*\\.exe"` - Code で始まる .exe
- `"chrome\\.exe|firefox\\.exe"` - chrome.exe または firefox.exe
- `".*game.*\\.exe"` - "game" を含む .exe（広すぎるので非推奨）

### 優先度の目安

```
95-100: 最優先（AFK検出、緊急状態）
80-94:  高優先（会議、重要な作業）
60-79:  中優先（開発作業、Steamゲーム）
40-59:  低優先（ブラウジング、一般アプリ）
0-39:   最低優先（フォールバック的な条件）
```

### Steamゲーム検出の設定

```yaml
options:
  steam_library_paths:
    - "C:\\Program Files (x86)\\Steam\\steamapps\\common"
    - "D:\\SteamLibrary\\steamapps\\common"
    # バックスラッシュは \\ でエスケープ
```

### よくある編集パターン

#### 1. 新しいゲームを追加

```yaml
rules:
  - name: specific game
    priority: 65
    when:
      any:
        - process: "GameProcess\\.exe"  # プロセス名（タスクマネージャーで確認）
    set:
      preset: "gaming"
```

#### 2. 新しいアプリを検出

```yaml
rules:
  - name: photo editing
    priority: 60
    when:
      all:
        - foreground_app: "Photoshop\\.exe|GIMP.*\\.exe"
    set:
      preset: "creative_work"  # 事前にpresetsで定義が必要

presets:
  creative_work:
    details: "画像編集中"
    state: "参加OK"
    assets:
      large_image: "design"
```

#### 3. 時間帯別の設定（条件の組み合わせ）

```yaml
rules:
  - name: long idle
    priority: 95
    when:
      all:
        - idle_gte_sec: 1800  # 30分以上
    set:
      preset: "status_afk"
```

#### 4. 複数条件の組み合わせ

```yaml
rules:
  - name: coding with music
    priority: 65
    when:
      all:
        - foreground_app: "Code\\.exe"
        - process: "Spotify\\.exe"
    set:
      preset: "focused_coding"
```

## コーディング規約

### Python

- **フォーマット**: PEP 8準拠
- **型ヒント**: 関数の引数と戻り値に型ヒントを使用
- **docstring**: 複雑な関数には必ず追加
- **エラーハンドリング**: try-exceptで適切に処理し、ログ出力

### YAML

- **インデント**: スペース2個
- **文字列**: 特殊文字がない限りクォート不要
- **パス**: Windows パスは `\\` でエスケープ（`C:\\Users\\...`）
- **正規表現**: バックスラッシュは `\\` でエスケープ（`Code\\.exe`）

## ファイル構成

```
discord_presence/
├── main.py         # エントリーポイント、メインループ
├── sensors.py      # システム状態検出（Windows API、Steam検出）
├── rules.py        # ルール評価エンジン
├── rpc_client.py   # Discord RPC通信
└── tray.py         # システムトレイUI

config.yaml         # 設定ファイル（個人情報含む、Gitに含めない）
config.yaml.example # サンプル設定（配布用）
```

## 重要な注意事項

### config.yamlの編集時

1. **バックアップを取る**: 編集前に必ずコピーを保存
2. **YAMLの構文**: インデントが重要（スペースのみ、タブ不可）
3. **正規表現のエスケープ**: `.` は `\\.` にする
4. **パスのエスケープ**: Windows パスは `\\` を使用
5. **app_id**: 個人のDiscord App IDは絶対にGitにコミットしない

### 新機能追加時

1. **センサー追加**: `sensors.py` の `Snapshot` dataclassにフィールド追加
2. **条件追加**: `rules.py` の `_condition_ok()` に条件ロジック追加
3. **テスト**: `test_rules.py` でテストケース追加
4. **ドキュメント**: README.mdを更新

## トラブルシューティング

### YAMLパースエラー

```python
# エラー確認
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### ルールが動作しない

1. 優先度を確認（高い数値が優先）
2. 正規表現を確認（`\\.exe` など）
3. ログを確認（実行時のコンソール出力）
4. `test_rules.py` でテスト

### プロセス名の確認方法

```python
import psutil
for proc in psutil.process_iter(['name']):
    print(proc.info['name'])
```

## Copilotへの指示例

### config.yaml編集時

```
# 良い例
"config.yamlにVALORANTを検出するルールを追加して。優先度は65で、gamingプリセットを使用"

"config.yamlのAFK検出時間を1時間（3600秒）に変更して"

"Spotify再生中のプリセットを追加して。detailsは「音楽聴いてる」、stateは「参加OK」で"

# 避けるべき例（情報不足）
"ゲーム追加して" → どのゲーム？プロセス名は？
"ルール変更" → どのルール？どう変更？
```

### コード編集時

```
# 良い例
"sensors.pyにCPU使用率を検出する機能を追加して。Snapshotにcpu_percentフィールドを追加"

"rules.pyにcpu_gte_percent条件を追加して。指定したCPU使用率以上の場合にマッチ"

# 詳細な指示
"config.yamlにDiscordアプリ検出のルールを追加。foreground_appで Discord.exe をチェック。優先度50で、chattingプリセット（新規作成）を使用。detailsは「チャット中」"
```

## 参考リンク

- [Discord Developer Portal](https://discord.com/developers/applications)
- [pypresence Documentation](https://qwertyquerty.github.io/pypresence/html/index.html)
- [Python Regular Expressions](https://docs.python.org/3/library/re.html)
- [YAML Syntax](https://yaml.org/spec/1.2.2/)
