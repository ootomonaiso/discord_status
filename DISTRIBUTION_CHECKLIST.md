# 配布前チェックリスト

## ✅ 完了項目

### セキュリティ
- [x] `config.yaml` に個人のDiscord App IDが含まれていないことを確認（空文字列に設定済み）
- [x] `config.yaml.example` を作成（サンプル設定）
- [x] `.gitignore` に `config.yaml` を追加
- [x] `.gitignore` にスタートアップスクリプトを追加（個人パスが含まれるため）
- [x] Steamライブラリパスがサンプル設定になっていることを確認

### ドキュメント
- [x] 詳細なREADME.mdを作成
  - インストール手順
  - Discord Developer Portal設定手順
  - 使い方
  - トラブルシューティング
  - カスタマイズ方法
- [x] `.gitignore` を作成

### 配布ファイル
以下のファイルがGitHubにプッシュされます：

```
discord-presence-manager/
├── discord_presence/          # ソースコード
│   ├── __init__.py
│   ├── main.py
│   ├── rpc_client.py
│   ├── sensors.py
│   ├── rules.py
│   └── tray.py
├── config_editor.py           # GUI設定エディタ
├── build_exe.py               # EXEビルドスクリプト
├── create_startup_scripts.py  # スタートアップスクリプト生成
├── test_rules.py              # テストスクリプト
├── test_sensors.py            # テストスクリプト
├── config.yaml.example        # 設定ファイルサンプル（重要！）
├── requirements.txt           # 依存パッケージ
├── .gitignore                 # Git除外設定
└── README.md                  # ドキュメント
```

### 除外されるファイル（.gitignore）
以下は個人情報が含まれるため、Gitには含まれません：

- `config.yaml` - 個人のDiscord App IDとSteamパスが含まれる
- `start_discord_presence.bat` - 個人のパスが含まれる
- `start_discord_presence.vbs` - 個人のパスが含まれる
- `.venv/` - 仮想環境
- `build/`, `dist/` - ビルド成果物
- `__pycache__/`, `*.pyc` - Pythonキャッシュ

## 📋 配布前の最終確認

1. **config.yaml.example の確認**
   ```bash
   cat config.yaml.example
   ```
   - `app_id: "YOUR_DISCORD_APP_ID"` になっているか
   - Steamパスがサンプルになっているか

2. **README.md の確認**
   - セットアップ手順が明確か
   - Discord Developer Portal設定が説明されているか

3. **個人情報の確認**
   ```bash
   # 個人情報が含まれていないか検索
   git grep -i "ootom"
   git grep -i "1434470162253353012"  # 実際のApp ID
   ```

## 🚀 GitHubへのプッシュ手順

```bash
# Gitリポジトリを初期化（まだの場合）
git init

# .gitignore が正しく動作しているか確認
git status

# 除外されるべきファイルがリストに含まれていないことを確認
# - config.yaml
# - start_discord_presence.bat
# - start_discord_presence.vbs

# ファイルを追加
git add .

# コミット
git commit -m "Initial commit: Discord Rich Presence Manager"

# GitHubでリポジトリを作成後、リモートを追加
git remote add origin https://github.com/YOUR_USERNAME/discord-presence-manager.git

# プッシュ
git push -u origin main
```

## 📝 リリース時の注意事項

### ユーザーへの指示（README.mdに記載済み）

1. `config.yaml.example` を `config.yaml` にコピー
2. Discord Developer Portalでアプリケーションを作成
3. `config.yaml` の `app_id` を設定
4. Steamパスを自分の環境に合わせて設定

### 追加で提供すると良いもの

- **スクリーンショット**: トレイアイコンやDiscordでの表示例
- **アセット画像サンプル**: Discord Developer Portalにアップロードする画像の例
- **動画デモ**: 使い方を示す短い動画

## ✨ 完了！

これでGitHubに安全に公開できます。
個人情報は一切含まれていません。
