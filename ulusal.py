import requests
import yaml
import json
import os
from datetime import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor

CONFIG_FILE = "config.json"
YAML_FILE = "streams.yaml"
M3U_FILE = "streams.m3u8"

# Kanal isimleri ve sayfa linkleri
CHANNELS = {
    "teve2": "https://www.teve2.com.tr/canli-yayin",
    "showtv": "https://www.showtv.com.tr/canli-yayin",
    "startv": "https://www.startv.com.tr/canli-yayin",
    "nowtv": "https://www.nowtv.com.tr/canli-yayin",
    "atv": "https://www.atv.com.tr/webtv/canli-yayin",
    "a2": "https://www.atv.com.tr/webtv/canli-yayin",
    "beyaztv": "https://www.beyaztv.com.tr/canli-yayin",
    "trt1": "https://www.trt1.com.tr/canli-yayin",
    "trtspor": "https://www.trtspor.com.tr/canli-yayin",
    "kanald": "https://www.kanald.com.tr/canli-yayin",
    "ntv": "https://www.ntv.com.tr/canli-yayin",
    "haberturk": "https://www.haberturk.com/canli-yayin",
    "dmax": "https://www.dmax.com.tr/canli-izle",
    "ekolspor": "https://www.ekoltv.com.tr/canli-yayin",
    "htspor": "https://www.haberturk.com/htspor/canli-yayin",
    "aspor": "https://www.aspor.com.tr/canli-yayin"
}

# Kesin fallback linkler
FALLBACK_LINKS = {
    "teve2": "https://demiroren.daioncdn.net/teve2/teve2.m3u8",
    "showtv": "https://tv.ensonhaber.com/tv/showtv.m3u8",
    "startv": "https://tv.ensonhaber.com/tv/startv.m3u8",
    "trt1": "https://tv-trt1.medya.trt.com.tr/master.m3u8",
    "trtspor": "https://tv-trtspor1.medya.trt.com.tr/master.m3u8",
    "aspor": "https://tv-aspor.medya.trt.com.tr/master.m3u8",
    "kanald": "https://demiroren.daioncdn.net/kanald/kanald.m3u8",
    "ntv": "https://dogus-live.daioncdn.net/ntv/playlist.m3u8",
    "haberturk": "https://ciner-live.daioncdn.net/haberturk/haberturktv.m3u8",
    "htspor": "https://htspor.medya.trt.com.tr/master.m3u8",
    "ekolspor": "https://ekolspor.medya.trt.com.tr/master.m3u8",
    "dmax": "https://dmax.medya.trt.com.tr/master.m3u8",
    "beyaztv": "https://beyaztv.medya.trt.com.tr/master.m3u8",
    "a2": "https://a2tv.medya.trt.com.tr/master.m3u8",
    "atv": "https://tv-atv.medya.trt.com.tr/master.m3u8",
    "nowtv": "https://nowtv.medya.trt.com.tr/master.m3u8"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/116.0.0.0 Safari/537.36"
}

def get_stream(channel_name, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        html = r.text
        start = html.find(".m3u8")
        if start != -1:
            link_start = html.rfind("https://", 0, start)
            link = html[link_start:start+len(".m3u8")]
            return link
    except Exception:
        pass
    # Fallback link kesin kullanılsın
    fallback = FALLBACK_LINKS.get(channel_name)
    if fallback:
        print(f"⚠️ {channel_name}: Yedek link kullanıldı.")
        return fallback
    print(f"❌ {channel_name}: Link bulunamadı!")
    return None

def fetch_channel(name_url):
    name, url = name_url
    link = get_stream(name, url)
    return name, link

def update_streams():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"output_path": "output/channels.txt", "streams": {}}, f, indent=2)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    streams = {}

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_channel, CHANNELS.items())

    for name, link in results:
        streams[name] = {"url": link, "updated": datetime.now().isoformat()}

    config["streams"] = streams
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # YAML
    with open(YAML_FILE, "w", encoding="utf-8") as f:
        yaml.dump(streams, f, allow_unicode=True)

    # M3U8
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, data in streams.items():
            if data["url"]:
                f.write(f"#EXTINF:-1,{name}\n")
                f.write(f"{data['url']}\n")

    # channels.txt
    output_path = config.get("output_path", "output/channels.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for name, data in streams.items():
            if data["url"]:
                f.write(f"{name}: {data['url']}\n")

    print(f"✅ {len(streams)} kanal güncellendi ve M3U8 dosyası oluşturuldu.")

if __name__ == "__main__":
    update_streams()
