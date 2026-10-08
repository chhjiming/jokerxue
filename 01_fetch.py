# -*- coding: utf-8 -*-
"""
批量抓取歌词草稿。
依赖：requests, beautifulsoup4
安装：pip install requests beautifulsoup4
"""

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
SONGS_FILE = os.path.join(BASE, "songs.txt")
DRAFTS_DIR = os.path.join(BASE, "drafts")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 元信息行，需要剔除
EXCLUDE_PATTERNS = [
    r"^作词[：:]", r"^作曲[：:]", r"^编曲[：:]", r"^制作人[：:]",
    r"^混音[：:]", r"^录音[：:]", r"^和声[：:]", r"^吉他[：:]",
    r"^贝斯[：:]", r"^鼓[：:]", r"^弦乐[：:]", r"^监制[：:]",
    r"^出品[：:]", r"^发行[：:]", r"^OP[：:]", r"^SP[：:]",
    r"^词[：:]", r"^曲[：:]", r"^编[：:]",
]

def clean_line(line):
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"^[\d]+[\.、]\s*", "", line)
    return line

def is_excluded(line):
    for pat in EXCLUDE_PATTERNS:
        if re.match(pat, line):
            return True
    return False

import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com",  # 关键，不加会返回403[citation:18]
}

def search_song_id(song_name):
    """搜索歌曲，返回第一个匹配的歌曲 id"""
    url = "https://music.163.com/api/search/get"
    params = {"s": song_name, "type": 1, "limit": 1}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        data = r.json()
        songs = data.get("result", {}).get("songs", [])
        if songs:
            return songs[0]["id"]
    except Exception as e:
        print(f"  [搜索失败] {song_name}: {e}")
    return None


def fetch_from_netease(song_name):
    """从网易云获取歌词，返回纯文本歌词或空字符串"""
    song_id = search_song_id(song_name)
    if not song_id:
        return ""

    url = f"https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        lrc = data.get("lrc", {}).get("lyric", "")
        if not lrc:
            return ""

        # 清洗 LRC：去掉时间标签 [00:00.00]，保留纯歌词
        lines = []
        for line in lrc.splitlines():
            if line.startswith("[") and "]" in line:
                text = line.split("]", 1)[1].strip()
                if text:
                    lines.append(text)
        return "\n".join(lines)
    except Exception as e:
        print(f"  [歌词获取失败] {song_name}: {e}")
        return ""

def main():
    if not os.path.exists(SONGS_FILE):
        print(f"找不到 {SONGS_FILE}")
        return

    os.makedirs(DRAFTS_DIR, exist_ok=True)

    with open(SONGS_FILE, encoding="utf-8") as f:
        songs = [line.strip() for line in f if line.strip()]

    for i, song in enumerate(songs, 1):
        print(f"[{i}/{len(songs)}] {song}")
        draft_path = os.path.join(DRAFTS_DIR, f"{song}.txt")

        if os.path.exists(draft_path):
            print("  草稿已存在，跳过")
            continue

        text = fetch_from_netease(song)
        if text:
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  已保存草稿：{len(text)} 字")
        else:
            # 也生成空草稿，方便你手动填
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write("")
            print("  未抓到，生成空草稿待手动填写")

        delay = random.uniform(3, 8)
        print(f"  等待 {delay:.1f} 秒…")
        time.sleep(delay)

    print("\n完成。请打开 drafts 文件夹人工校对，然后运行 02_merge.py")

if __name__ == "__main__":
    main()