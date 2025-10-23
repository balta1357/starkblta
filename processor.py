# processor.py

import subprocess
import requests
import re
import os
import json
import time
import copy
import html
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

M3U8_DIR = "m3u8"
CONFIG_FILE = "config.json"
LOG_FILE = "log.txt"

def log(message):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    print(f"[{timestamp}] {message}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except IOError:
        pass

def sanitize_filename(filename):
    replacements = {'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u','Ç':'C','Ğ':'G','İ':'I','Ö':'O','Ş':'S','Ü':'U'}
    for tr, en in replacements.items():
        filename = filename.replace(tr, en)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'[^A-Za-z0-9_.-]', '', filename)
    return filename or "KANAL"

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            channels_raw = data.get("channels", [])
            channels = [ch if len(ch) == 3 else ch + [False] for ch in channels_raw]
            return channels, data.get("ONLY_HIGHEST", 1)
    except Exception as e:
        log(f"Config dosyası okunamadı: {e}")
        return [], 1

def scrape_m3u8_from_website(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        content = r.text
        patterns = [r'(https?://[^\s"\'`<>]+?\.m3u8)']
        for p in patterns:
            matches = re.findall(p, content)
            if matches:
                return html.unescape(matches[0])
    except Exception as e:
        log(f"Site tarama hatası ({url}): {e}")
    return None

def get_youtube_m3u8_url(video_or_channel_id):
    headers = {'User-Agent': 'Mozilla/5.0'}
    video_id = None

    if not video_or_channel_id.startswith(('UC', '@')):
        video_id = video_or_channel_id
    else:
        live_url = f"https://www.youtube.com/channel/{video_or_channel_id}/live" if video_or_channel_id.startswith('UC') else f"https://www.youtube.com/{video_or_channel_id}/live"
        try:
            r = requests.get(live_url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            canonical = soup.find("link", rel="canonical")
            if canonical and "href" in canonical.attrs:
                m = re.search(r"v=([a-zA-Z0-9_-]{11})", canonical["href"])
                if m:
                    video_id = m.group(1)
        except Exception:
            return None

    if not video_id:
        return None

    params = {'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'}
    json_data = {'context': {'client': {'clientName': 'WEB', 'clientVersion': '2.20231101.05.00'}}, 'videoId': video_id}
    try:
        r = requests.post('https://www.youtube.com/youtubei/v1/player', params=params, headers=headers, json=json_data)
        r.raise_for_status()
        return r.json().get("streamingData", {}).get("hlsManifestUrl")
    except Exception as e:
        log(f"YouTube M3U8 hatası ({video_id}): {e}")
        return None

def get_resolution_label(height):
    if height >= 1080: return " FULL HD"
    if height >= 720: return " HD"
    if height > 0: return " SD"
    return ""

def get_github_details_from_remote():
    try:
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], check=True, capture_output=True, text=True)
        url = res.stdout.strip()
        m = re.search(r'(?:[:/])([^/]+)/([^/]+?)(?:\.git)?$', url)
        if m:
            return m.group(1), m.group(2)
    except Exception as e:
        log(f"GitHub detay hatası: {e}")
    return None, None

def generate_master_playlist(channel_data, user, repo):
    base_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{M3U8_DIR}"
    content = ['#EXTM3U']
    for ch in channel_data:
        name, label = ch['name'], ch['label']
        filename = f"{sanitize_filename(name).upper()}.m3u8"
        full_url = f"{base_url}/{filename}"
        content.extend([f'#EXTINF:-1,{name}{label}', full_url])
    with open("tv.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    log("tv.m3u8 oluşturuldu.")

def main():
    log("="*30)
    log("GitHub Actions M3U8 İşleyici Başladı")
    log("="*30)

    channels, only_highest = load_config()
    os.makedirs(M3U8_DIR, exist_ok=True)
    playlist_data = []

    for name, src, _ in channels:
        log(f"İşleniyor: {name}")
        master_url = None

        if src.startswith(("http://", "https://")):
            master_url = scrape_m3u8_from_website(src)
        else:
            master_url = get_youtube_m3u8_url(src)

        if not master_url:
            log(f"{name}: M3U8 bulunamadı.")
            playlist_data.append({'name': name, 'label': ''})
            continue

        try:
            r = requests.get(master_url, timeout=30)
            lines = r.text.splitlines()
            streams = []
            max_h = 0
            for i, line in enumerate(lines):
                if line.startswith("#EXT-X-STREAM-INF"):
                    m = re.search(r'RESOLUTION=\d+x(\d+)', line)
                    h = int(m.group(1)) if m else 0
                    if i+1 < len(lines):
                        u = lines[i+1]
                        if not u.startswith("http"):
                            u = urljoin(master_url, u)
                        streams.append({'line': line, 'url': u, 'height': h})
                        max_h = max(max_h, h)
            label = get_resolution_label(max_h)
            playlist_data.append({'name': name, 'label': label})
            if only_highest and streams:
                s = max(streams, key=lambda x: x['height'])
                final = '\n'.join(['#EXTM3U', s['line'], s['url']])
            else:
                parts = ['#EXTM3U']
                for s in sorted(streams, key=lambda x: x['height'], reverse=True):
                    parts.extend([s['line'], s['url']])
                final = '\n'.join(parts)
            filename = f"{sanitize_filename(name).upper()}.m3u8"
            with open(os.path.join(M3U8_DIR, filename), "w", encoding="utf-8") as f:
                f.write(final)
            log(f"{filename} oluşturuldu.")
        except RequestException as e:
            log(f"{name}: Hata {e}")

    user, repo = get_github_details_from_remote()
    if user and repo:
        generate_master_playlist(playlist_data, user, repo)
    log("Tamamlandı.")

if __name__ == "__main__":
    main()
