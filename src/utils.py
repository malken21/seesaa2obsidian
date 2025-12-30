"""Utility functions for Seesaa Wiki to Obsidian converter."""
import re
import urllib.parse
from urllib.parse import quote, unquote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session() -> requests.Session:
    """Create a requests session with retry logic.

    Returns:
        requests.Session: Configured session object.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    session.mount('http://', HTTPAdapter(max_retries=retries))
    return session


def sanitize_filename(title: str) -> str:
    """Sanitize a string to be safe for use as a filename.

    Args:
        title (str): The original title.

    Returns:
        str: Sanitized filename.
    """
    title = re.sub(r'[\\/*?:"<>|]', '_', title)
    title = title.replace('\n', '').replace('\r', '').strip()
    return title[:100]


def clean_markdown(text: str) -> str:
    """Clean up markdown text.

    Removes excessive newlines.

    Args:
        text (str): Raw markdown text.

    Returns:
        str: Cleaned markdown text.
    """
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def encode_seesaa_url(path: str) -> str:
    """Encode URL path component using EUC-JP (euc_jis_2004).

    Seesaa Wiki requires the path part to be EUC-JP encoded.
    Uses euc_jis_2004 to support circular numbers (e.g., ⑨).

    Args:
        path (str): The path component to encode.

    Returns:
        str: Percent-encoded string.
    """
    try:
        # If already percent-encoded, decode first
        decoded = unquote(path)
        # safe='/' is default, so slashes are not encoded
        return quote(decoded.encode('euc_jis_2004'))
    except Exception:
        # Fallback to UTF-8 if encoding fails
        return quote(path)


def decode_seesaa_url(url: str) -> str:
    """Decode Seesaa Wiki URL (EUC-JP encoded) to string.

    Args:
        url (str): The URL to decode.

    Returns:
        str: Decoded string.
    """
    try:
        # Unquote first to get bytes (latin-1 preserves bytes)
        unquoted = unquote(url, encoding='latin-1')
        bytes_url = unquoted.encode('latin-1')
        return bytes_url.decode('euc_jis_2004')
    except Exception:
        # Fallback to UTF-8 (standard unquote) if EUC-JP decoding fails
        return unquote(url)
