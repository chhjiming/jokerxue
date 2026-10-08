# -*- coding: utf-8 -*-
"""
把 drafts 文件夹里校对好的歌词合并进 lyrics.json。
空文件会被跳过，不覆盖已有歌词（除非加 --force）。
"""

import os
import json
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DRAFTS_DIR = os.path.join(BASE, "drafts")
LYRICS_FILE = os.path.join(BASE, "lyrics.json")

force = "--force" in sys.argv

def load_json(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    if not os.path.isdir(DRAFTS_DIR):
        print(f"找不到 {DRAFTS_DIR}")
        return

    lyrics = load_json(LYRICS_FILE)
    added, updated, skipped = 0, 0, 0

    for name in sorted(os.listdir(DRAFTS_DIR)):
        if not name.endswith(".txt"):
            continue
        song = name[:-4]
        with open(os.path.join(DRAFTS_DIR, name), encoding="utf-8") as f:
            text = f.read().strip()

        if not text:
            print(f"  跳过空草稿：{song}")
            skipped += 1
            continue

        if song in lyrics and lyrics[song] and not force:
            print(f"  已有歌词，跳过：{song}（加 --force 可覆盖）")
            skipped += 1
            continue

        if song in lyrics and lyrics[song]:
            updated += 1
        else:
            added += 1
        lyrics[song] = text

    save_json(LYRICS_FILE, lyrics)
    print(f"\n合并完成：新增 {added}，更新 {updated}，跳过 {skipped}")
    print(f"lyrics.json 共 {len(lyrics)} 首")

if __name__ == "__main__":
    main()