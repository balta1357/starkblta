import os
import shutil
import requests
import re
import sys
import yaml

# Terminal renkleri
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Klasör ve dosya yolu
stream_folder = "stream"
output_file = os.path.join(stream_folder, "all_channels.m3u")
extra_yaml_path = "extra_channels.yaml"

# === Kaynak 1: Webden çekilecek kanallar ===
source_urls = {
   "tabii": "https://www.tabii.com/tr/watch/live/trt1?trackId=150002",
    "nowtv": "https://www.nowtv.com.tr/canli-yayin",
    "showtv": "https://www.showtv.com.tr/canli-yayin",
    "startv": "https://puhutv.com/star-tv-canli-yayin",
    "tv8": "https://www.tv8.com.tr/canli-yayin",
    "tv8bucuk": "https://www.tv8bucuk.com/tv8-5-canli-yayin",
    "atv": "https://www.atv.com.tr/canli-yayin",
    "kanald": "https://www.kanald.com.tr/canli-yayin",
    "teve2": "https://www.teve2.com.tr/canli-yayin",
    "dmax": "https://www.dmax.com.tr/canli-izle",
    "tv360": "https://www.tv360.com.tr/canli-yayin",
    "beyaztv": "https://www.beyaztv.com.tr/canli-yayin",
    "cnnturk": "https://www.cnnturk.com/canli-yayin",
    "ntv": "https://puhutv.com/ntv-canli-yayin",
    "ekolspor": "https://www.ekoltv.com.tr/canli-yayin",
    "ulketv": "https://www.ulketv.com/ulke-tv-canli-yayin",
    "htspor": "https://www.htspor.com/canli-yayin",
    "haberturk": "https://www.haberturk.com/canliyayin",
   
}

# === Kaynak 2: TrGoals Kanalları ===
KANALLAR = [  # Kısaltılmış liste (önceki uzun listeyi kullanabilirsin)
    {"dosya": "yayinzirve.m3u8", "tvg_id": "BeinSports1.tr", "kanal_adi": "Bein Sports 1 HD (VIP)"},
    {"dosya": "yayin1.m3u8", "tvg_id": "BeinSports1.tr", "kanal_adi": "Bein Sports 1 HD"},
    {"dosya": "yayinb2.m3u8", "tvg_id": "BeinSports2.tr", "kanal_adi": "Bein Sports 2 HD"},
    {"dosya": "yayinb3.m3u8", "tvg_id": "BeinSports3.tr", "kanal_adi": "Bein Sports 3 HD"},
    {"dosya": "yayinb4.m3u8", "tvg_id": "BeinSports4.tr", "kanal_adi": "Bein Sports 4 HD"},
    {"dosya": "yayinb5.m3u8", "tvg_id": "BeinSports5.tr", "kanal_adi": "Bein Sports 5 HD"},
    {"dosya": "yayinbm1.m3u8", "tvg_id": "BeinMax1.tr", "kanal_adi": "Bein Max 1 HD"},
    {"dosya": "yayinbm2.m3u8", "tvg_id": "BeinMax2.tr", "kanal_adi": "Bein Max 2 HD"},
    {"dosya": "yayinss.m3u8", "tvg_id": "SSport1.tr", "kanal_adi": "S Sport 1 HD"},
    {"dosya": "yayinss2.m3u8", "tvg_id": "SSport2.tr", "kanal_adi": "S Sport 2 HD"},
    {"dosya": "yayinssp2.m3u8", "tvg_id": "SSportPlus.tr", "kanal_adi": "S Sport Plus HD"},
    {"dosya": "yayint1.m3u8", "tvg_id": "TivibuSpor1.tr", "kanal_adi": "Tivibu Spor 1 HD"},
    {"dosya": "yayint2.m3u8", "tvg_id": "TivibuSpor2.tr", "kanal_adi": "Tivibu Spor 2 HD"},
    {"dosya": "yayint3.m3u8", "tvg_id": "TivibuSpor3.tr", "kanal_adi": "Tivibu Spor 3 HD"},
    {"dosya": "yayinsmarts.m3u8", "tvg_id": "SmartSpor1.tr", "kanal_adi": "Smart Spor 1 HD"},
    {"dosya": "yayinsms2.m3u8", "tvg_id": "SmartSpor2.tr", "kanal_adi": "Smart Spor 2 HD"},
    {"dosya": "yayintrtspor.m3u8", "tvg_id": "TRTSpor.tr", "kanal_adi": "TRT Spor HD"},
    {"dosya": "yayintrtspor2.m3u8", "tvg_id": "TRTSporYildiz.tr", "kanal_adi": "TRT Spor Yıldız HD"},
    {"dosya": "yayinas.m3u8", "tvg_id": "ASpor.tr", "kanal_adi": "A Spor HD"},
    {"dosya": "yayinatv.m3u8", "tvg_id": "ATV.tr", "kanal_adi": "ATV HD"},
    {"dosya": "yayintv8.m3u8", "tvg_id": "TV8.tr", "kanal_adi": "TV8 HD"},
    {"dosya": "yayintv85.m3u8", "tvg_id": "TV85.tr", "kanal_adi": "TV8.5 HD"},
    {"dosya": "yayinnbatv.m3u8", "tvg_id": "NBATV.tr", "kanal_adi": "NBA TV HD"},
    {"dosya": "yayinex1.m3u8", "tvg_id": "ExxenSpor1.tr", "kanal_adi": "Exxen Spor 1 HD"},
    {"dosya": "yayinex2.m3u8", "tvg_id": "ExxenSpor2.tr", "kanal_adi": "Exxen Spor 2 HD"},
    {"dosya": "yayinex3.m3u8", "tvg_id": "ExxenSpor3.tr", "kanal_adi": "Exxen Spor 3 HD"},
    {"dosya": "yayinex4.m3u8", "tvg_id": "ExxenSpor4.tr", "kanal_adi": "Exxen Spor 4 HD"},
    {"dosya": "yayinex5.m3u8", "tvg_id": "ExxenSpor5.tr", "kanal_adi": "Exxen Spor 5 HD"},
    {"dosya": "yayinex6.m3u8", "tvg_id": "ExxenSpor6.tr", "kanal_adi": "Exxen Spor 6 HD"},
    {"dosya": "yayinex7.m3u8", "tvg_id": "ExxenSpor7.tr", "kanal_adi": "Exxen Spor 7 HD"},
    {"dosya": "yayinex8.m3u8", "tvg_id": "ExxenSpor8.tr", "kanal_adi": "Exxen Spor 8 HD"},
    # ...
]

# === Klasör işlemleri ===
if os.path.exists(stream_folder):
    shutil.rmtree(stream_folder)
os.makedirs(stream_folder)

# === Fonksiyonlar ===

def extract_m3u8(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        matches = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', r.text)
        return matches[0] if matches else None
    except Exception as e:
        print(f"{RED}[HATA] {url} -> {e}{RESET}")
        return None

def siteyi_bul():
    print(f"{YELLOW}[*] TrGoals sitesi aranıyor...{RESET}")
    for i in range(1400, 2454):
        url = f"https://trgoals{i}.xyz/"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and "channel.html?id=" in r.text:
                print(f"{GREEN}[✓] Yayın bulundu: {url}{RESET}")
                return url
        except requests.RequestException:
            continue
    print(f"{RED}[X] TrGoals sitesi bulunamadı.{RESET}")
    return None

def find_baseurl(channel_url):
    try:
        r = requests.get(channel_url, timeout=10)
        r.raise_for_status()
        match = re.search(r'baseurl\s*[:=]\s*["\']([^"\']+)["\']', r.text)
        return match.group(1) if match else None
    except requests.RequestException:
        return None

def load_extra_channels(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("extra_channels", [])
        except Exception as e:
            print(f"{RED}[HATA] extra_channels.yaml okunamadı: {e}{RESET}")
    return []

def write_combined_m3u8(filepath, web_links, trgoals_base_url, referer, user_agent, extra_channels):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("# === Web Kaynaklı Kanallar ===\n")
        for name, link in web_links.items():
            f.write(f"#EXTINF:-1,{name}\n{link}\n")

        f.write("\n# === TrGoals Kanalları ===\n")
        for kanal in KANALLAR:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{kanal["kanal_adi"]}",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={user_agent}\n')
            f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
            f.write(trgoals_base_url + kanal["dosya"] + "\n")

        f.write("\n# === Extra Manuel Eklenen Kanallar ===\n")
        for ch in extra_channels:
            f.write(f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-name="{ch["kanal_adi"]}",{ch["kanal_adi"]}\n')
            f.write(f"{ch['url']}\n")

    print(f"{GREEN}[✓] M3U dosyası oluşturuldu: {filepath}{RESET}")

# === Ana Akış ===
if __name__ == "__main__":
    print(f"{YELLOW}[*] Web kaynakları taranıyor...{RESET}")
    web_links = {}
    for name, url in source_urls.items():
        m3u8 = extract_m3u8(url)
        if m3u8:
            web_links[name] = m3u8
            print(f"{GREEN}[✓] {name} eklendi.{RESET}")
        else:
            print(f"{RED}[X] {name} için link bulunamadı.{RESET}")

    print(f"{YELLOW}[*] TrGoals linki bulunuyor...{RESET}")
    site = siteyi_bul()
    if not site:
        sys.exit(1)
    base_url = find_baseurl(site + "/channel.html?id=yayinzirve")
    if not base_url:
        print(f"{RED}[X] Base URL alınamadı.{RESET}")
        sys.exit(1)

    extra_channels = load_extra_channels(extra_yaml_path)

    write_combined_m3u8(
        output_file,
        web_links,
        base_url,
        site,
        "Mozilla/5.0",
        extra_channels
    )
