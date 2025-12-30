"""Main entry point for Seesaa Wiki to Obsidian converter."""
import sys
import os
import time

import config
import core
import utils


def main() -> None:
    """Execute the main scraping process."""
    if not config.BASE_URL:
        print("[エラー] 環境変数 BASE_URL が設定されていません。")
        sys.exit(1)

    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)

    session = utils.create_session()
    url_map = core.get_all_page_map(session)

    if not url_map:
        print("[終了] 処理対象がありません。")
        return

    # 重複除去と正規化 (coreに移動済み)
    unique_pages = core.process_page_map(url_map)

    total = len(unique_pages)
    count = 0
    
    for url, title in unique_pages.items():
        count += 1
        print(f"[{count}/{total}] ", end="")
        core.save_page(session, title, url, url_map)
        
        time.sleep(config.SLEEP_TIME)

    print("\n[完了] 全処理が終了しました。")


if __name__ == "__main__":
    main()
