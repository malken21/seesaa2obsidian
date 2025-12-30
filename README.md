# Seesaa Wiki to Obsidian Converter

Seesaa Wiki の記事を収集し、Obsidian で扱いやすい Markdown 形式に変換して保存するツールです。

## 使い方

1. `docker-compose.yml` を編集します。
   - `BASE_URL`: 取得したい Seesaa Wiki の URL を設定してください。
   - 必要に応じて `SLEEP_TIME` (待機時間) や `SKIP_EXISTING` (重複スキップ) などの設定も変更可能です。

2. 以下のコマンドを実行してツールを起動します。

```bash
docker compose up --build
```

収集されたデータは `./output` ディレクトリに保存されます。
