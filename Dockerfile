# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# 依存ライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトのコピー
COPY main.py .

# 実行ユーザー設定（任意：rootでの実行を避ける場合などに設定）
# 今回はシンプルさを優先しrootのままとする

# コンテナ起動時のコマンド
CMD ["python", "main.py"]