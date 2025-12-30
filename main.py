import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import os
import time
import re
import urllib.parse
import sys

# ==========================================
# 設定エリア (環境変数から取得、デフォルト値設定)
# ==========================================
WIKI_ID = os.getenv("WIKI_ID", "my_game_wiki")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
SLEEP_TIME = float(os.getenv("SLEEP_TIME", "1.0"))
TIMEOUT = int(os.getenv("TIMEOUT", "10"))
# "true"または"True"の場合に有効化
SKIP_EXISTING = os.getenv("SKIP_EXISTING", "false").lower() == "true"
# ==========================================

BASE_URL = f"https://seesaawiki.jp/{WIKI_ID}"
LIST_URL = f"{BASE_URL}/l"


def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


def sanitize_filename(title):
    title = re.sub(r'[\\/*?:"<>|]', '_', title)
    title = title.replace('\n', '').replace('\r', '').strip()
    return title[:100]


def clean_markdown(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_all_page_map(session):
    print(f"[処理開始] Wiki ID: {WIKI_ID}")
    print(f"[処理開始] ページ一覧を取得中: {LIST_URL}")
    url_map = {}

    try:
        response = session.get(LIST_URL, timeout=TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"[エラー] 一覧取得失敗: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    main_content = soup.find(id="content_block_main") or soup

    for a_tag in main_content.find_all('a', href=True):
        href = a_tag['href']
        title = a_tag.get_text().strip()

        if not title:
            continue

        if href.startswith('/'):
            full_url = f"https://seesaawiki.jp{href}"
        elif href.startswith('http'):
            full_url = href
        else:
            continue

        if f"seesaawiki.jp/{WIKI_ID}/d/" in full_url:
            decoded_url = urllib.parse.unquote(full_url)
            url_map[decoded_url] = title
            url_map[full_url] = title

    print(f"[完了] {len(url_map)} ページ分の情報をインデックス化しました。")
    return url_map


def convert_internal_links(markdown_text, url_map):
    def replacer(match):
        text = match.group(1)
        url = match.group(2)

        if url.startswith('/'):
            target_url = f"https://seesaawiki.jp{url}"
        else:
            target_url = url

        try:
            decoded_target = urllib.parse.unquote(target_url)
        except:
            decoded_target = target_url

        if decoded_target in url_map:
            dest_title = url_map[decoded_target]
            if text == dest_title:
                return f"[[{dest_title}]]"
            else:
                return f"[[{dest_title}|{text}]]"
        elif target_url in url_map:
            dest_title = url_map[target_url]
            if text == dest_title:
                return f"[[{dest_title}]]"
            else:
                return f"[[{dest_title}|{text}]]"

        return match.group(0)

    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replacer, markdown_text)


def save_page(session, title, url, url_map):
    filename = sanitize_filename(title) + ".md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # スキップ処理の実装
    if SKIP_EXISTING and os.path.exists(filepath):
        print(f"[スキップ] 既存ファイルあり: {title}")
        return

    print(f"ダウンロード中: {title}")

    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"  [失敗] {url} ({e})")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find(id="content_block_main") or soup.find(id="content")

    if not content_div:
        print("  [警告] 本文が見つかりません。")
        return

    for tag in content_div(['script', 'style', 'iframe', 'form', 'input', 'button']):
        tag.decompose()

    markdown_text = md(str(content_div), heading_style="atx")
    markdown_text = convert_internal_links(markdown_text, url_map)
    markdown_text = clean_markdown(markdown_text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"---\nurl: {url}\ntitle: {title}\n---\n\n")
        f.write(markdown_text)


def main():
    if not WIKI_ID:
        print("[エラー] 環境変数 WIKI_ID が設定されていません。")
        sys.exit(1)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    session = create_session()
    url_map = get_all_page_map(session)

    if not url_map:
        print("[終了] 処理対象がありません。")
        return

    total = len(url_map)
    processed_urls = set()

    count = 0
    for url, title in url_map.items():
        if url in processed_urls:
            continue
        if not url.startswith('http'):
            continue

        count += 1
        print(f"[{count}/{total}] ", end="")
        save_page(session, title, url, url_map)
        processed_urls.add(url)

        time.sleep(SLEEP_TIME)

    print("\n[完了] 全処理が終了しました。")


if __name__ == "__main__":
    main()
