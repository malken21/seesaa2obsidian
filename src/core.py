"""Core logic for Seesaa Wiki to Obsidian converter."""
import os
import re
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import requests

import config
import utils


def get_all_page_map(session: requests.Session) -> Dict[str, str]:
    """Retrieve all pages from Seesaa Wiki and map URLs to titles.

    Args:
        session (requests.Session): Active requests session.

    Returns:
        Dict[str, str]: Dictionary mapping URLs to page titles.
    """
    print(f"[処理開始] Target Wiki: {config.BASE_URL}")
    
    current_url: Optional[str] = config.LIST_URL
    url_map: Dict[str, str] = {}
    
    while current_url:
        print(f"[処理開始] ページ一覧を取得中: {current_url}")
        
        try:
            response = session.get(current_url, timeout=config.TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except Exception as e:
            print(f"[エラー] 一覧取得失敗: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        # メインコンテンツの特定 (Seesaa Wikiの構造に合わせて調整)
        main_content = soup.find(id="main") or soup.find(id="content_block_main") or soup

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

            # BASE_URLが含まれるかチェック (以前は config.WIKI_ID を使用していた部分)
            if full_url.startswith(f"{config.BASE_URL}/d/"):
                # EUC-JPとしてデコードして格納
                decoded_title = utils.decode_seesaa_url(full_url)
                
                # デコードされたURL(日本語含む) -> タイトル
                url_map[decoded_title] = title
                
                # 生のURL -> タイトル
                url_map[full_url] = title

        # 次のページを探す
        next_link = soup.select_one('li.next a')
        if next_link:
            next_href = next_link.get('href')
            if next_href:
                if next_href.startswith('/'):
                     current_url = f"https://seesaawiki.jp{next_href}"
                else:
                     current_url = next_href
            else:
                current_url = None
        else:
            current_url = None

    print(f"[完了] {len(url_map)} ページ分の情報をインデックス化しました。")
    return url_map


def process_page_map(url_map: Dict[str, str]) -> Dict[str, str]:
    """Process and normalize the URL map.

    Deduplicates entries by decoding URLs and ensuring unique keys.

    Args:
        url_map (Dict[str, str]): Raw URL map with potentially mixed keys.

    Returns:
        Dict[str, str]: Normalized map where keys are decoded URLs.
    """
    unique_pages = {}
    for url, title in url_map.items():
        if not url.startswith('http'):
            continue
        decoded_url = utils.decode_seesaa_url(url)
        unique_pages[decoded_url] = title
    return unique_pages


def convert_internal_links(markdown_text: str, url_map: Dict[str, str]) -> str:
    """Convert Seesaa Wiki internal links to Obsidian style links.

    Args:
        markdown_text (str): The raw markdown text.
        url_map (Dict[str, str]): Map of URLs to page titles.

    Returns:
        str: Markdown text with converted links.
    """
    def replacer(match: re.Match) -> str:
        text = match.group(1)
        url = match.group(2)

        if url.startswith('/'):
            target_url = f"https://seesaawiki.jp{url}"
        else:
            target_url = url

        # リンク先URLをデコードしてタイトルを探す
        decoded_target = utils.decode_seesaa_url(target_url)

        dest_title = None
        if decoded_target in url_map:
            dest_title = url_map[decoded_target]
        elif target_url in url_map:
            dest_title = url_map[target_url]

        if dest_title:
            if text == dest_title:
                return f"[[{dest_title}]]"
            else:
                return f"[[{dest_title}|{text}]]"

        return match.group(0)

    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    return re.sub(pattern, replacer, markdown_text)


def save_page(session: requests.Session, title: str, url: str, url_map: Dict[str, str]) -> None:
    """Download and save a single page content as markdown.

    Args:
        session (requests.Session): Active requests session.
        title (str): Page title.
        url (str): Page URL (unused directly, reconstructed from title).
        url_map (Dict[str, str]): URL map for link conversion.
    """
    filename = utils.sanitize_filename(title) + ".md"
    filepath = os.path.join(config.OUTPUT_DIR, filename)

    if config.SKIP_EXISTING and os.path.exists(filepath):
        print(f"[スキップ] 既存ファイルあり: {title}")
        return

    # URLを正しく再構築する (URLエンコード対策)
    encoded_page_name = utils.encode_seesaa_url(title)
    target_url = f"{config.BASE_URL}/d/{encoded_page_name}"
    
    print(f"Downloading: {title}")

    try:
        response = session.get(target_url, timeout=config.TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"  [失敗] {target_url} ({e})")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    # 本文の抽出: class="user-area" が記事本文
    content_div = soup.find("div", class_="user-area") or soup.find(id="page-body") or soup.find(id="content_block_main")

    if not content_div:
        print("  [警告] 本文が見つかりません。")
        return

    for tag in content_div(['script', 'style', 'iframe', 'form', 'input', 'button']): # type: ignore
        tag.decompose()

    markdown_text = md(str(content_div), heading_style="atx")
    markdown_text = convert_internal_links(markdown_text, url_map)
    markdown_text = utils.clean_markdown(markdown_text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"---\nurl: {target_url}\ntitle: {title}\n---\n\n")
        f.write(markdown_text)

