# main.py
import re
import requests
from yt_dlp import YoutubeDL
from datetime import datetime

COOKIE_FILE = "cookies.txt"  # GitHub Actions'ta secrets ile oluşturulacak

def get_live_video_id(channel_url: str):
    """
    Verilen YouTube kanalındaki aktif canlı yayın ID'sini bulur.
    """
    url = f"https://www.youtube.com/{channel_url}/live"
    print(f"[CHECK] {url} kontrol ediliyor...")
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", response)
        return match.group(1) if match else None
    except Exception as e:
        print(f"[ERROR] {channel_url} kontrol edilirken hata oluştu: {e}")
        return None

def create_m3u(channel_name: str, video_id: str):
    """
    Belirtilen video ID'den .m3u dosyası oluşturur.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "cookies": COOKIE_FILE,  # Cookie dosyasını kullan
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info["url"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{channel_name}_{timestamp}.m3u"

        with open(filename, "w") as f:
            f.write("#EXTM3U\n")
            f.write(f"#EXTINF:-1,{channel_name} (YouTube)\n")
            f.write(stream_url + "\n")

        print(f"[OK] {filename} oluşturuldu.")

    except Exception as e:
        print(f"[ERROR] {channel_name} M3U oluşturulamadı: {e}")

if __name__ == "__main__":
    channels = {
        "SozcuTV": "@sozcuhaber",
        "HalkTV": "@HalkTVCanli",
        "FOXHaber": "@FOXhaber",
        "NTV": "@ntv",
        "KRTHaber": "@krthaber",
        "SifirTV": "@sifirtv",
        "ASpor": "@aspor",
        "HTSpor": "@htspor",
    }

    for name, channel in channels.items():
        video_id = get_live_video_id(channel)
        if video_id:
            create_m3u(name, video_id)
        else:
            print(f"[NO LIVE] {name} şu anda canlı değil.\n")
