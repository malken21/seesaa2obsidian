"""Configuration module for Seesaa Wiki to Obsidian converter.

This module loads environment variables and sets up configuration constants.
"""
import os

# ==========================================
# 設定エリア (環境変数から取得、デフォルト値設定)
# ==========================================
BASE_URL: str = os.getenv("BASE_URL", "").rstrip("/")
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
SLEEP_TIME: float = float(os.getenv("SLEEP_TIME", "1.0"))
TIMEOUT: int = int(os.getenv("TIMEOUT", "10"))
# "true"または"True"の場合に有効化
SKIP_EXISTING: bool = os.getenv("SKIP_EXISTING", "false").lower() == "true"
# ==========================================

LIST_URL: str = f"{BASE_URL}/l/"

