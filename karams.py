import requests
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# --------------------
# Ayarlar
LAST_FILE = Path("last_index.txt")
LAST_FOUND_FILE = Path("last_found.txt")  # bulunduysa tam URL buraya kaydedilir
DEFAULT_START = 1300
THREAD_SAYISI = 30
BATCH_SIZE = THREAD_SAYISI
SLEEP_BETWEEN_BATCHES = 0.15
MAX_EMPTY_BATCHES = None
REQUEST_TIMEOUT = 4
# Domain patternleri (isteğe göre yeni pattern / tld ekle)
PREFIX_PATTERNS = [
    "trgoals{n}",         # orijinal
    "trgoals-{n}",
    "trgoals{n}tv",
    "trgoals{n}-tv",
    "trgoals{n}online",
    "trgoal{n}",
]
TLDS = [".xyz", ".com", ".net", ".site", ".online"]
# --------------------

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

KANALLAR = [
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
]

dur_event = threading.Event()
found_lock = threading.Lock()
found_result = {"url": None, "index": None}

def read_last_index():
    try:
        if LAST_FILE.exists():
            return int(LAST_FILE.read_text().strip())
    except Exception:
        pass
    return None

def write_last_index(idx):
    try:
        LAST_FILE.write_text(str(int(idx)))
    except Exception:
        print(f"{YELLOW}[Uyarı] last_index.txt yazılamadı.{RESET}")

def read_last_found():
    try:
        if LAST_FOUND_FILE.exists():
            txt = LAST_FOUND_FILE.read_text().strip()
            if txt:
                return txt
    except Exception:
        pass
    return None

def write_last_found(url):
    try:
        LAST_FOUND_FILE.write_text(url)
    except Exception:
        print(f"{YELLOW}[Uyarı] last_found.txt yazılamadı.{RESET}")

def generate_candidate_domains(i):
    """PREFIX_PATTERNS ve TLDS kullanarak domain adlarını üret."""
    for p in PREFIX_PATTERNS:
        name = p.format(n=i)
        for t in TLDS:
            yield f"https://{name}{t}/"

def kontrol_et(i):
    """Artık her index için çeşitli domain pattern'lerini dener."""
    if dur_event.is_set():
        return None
    # Eğer last_found varsa önce onu kontrol et (tek seferlik hızlı doğrulama)
    last_found = read_last_found()
    if last_found:
        try:
            r = requests.get(last_found, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200 and "channel.html?id=" in r.text:
                with found_lock:
                    if not found_result["url"]:
                        found_result["url"] = last_found
                        found_result["index"] = i  # index bilinmiyorsa i yaz (yaklaşık)
                write_last_found(last_found)
                dur_event.set()
                print(f"{GREEN}[OK] Önceden kayıtlı domain hâlâ canlı: {last_found}{RESET}")
                return (i, last_found)
        except requests.RequestException:
            # kayıtlı domain çalışmıyor, devam edilecek
            pass

    # Aşağıda i için oluşturulan kombinasyonları dener
    for candidate in generate_candidate_domains(i):
        if dur_event.is_set():
            return None
        try:
            r = requests.get(candidate, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                if "channel.html?id=" in r.text:
                    with found_lock:
                        if not found_result["url"]:
                            found_result["url"] = candidate
                            found_result["index"] = i
                    write_last_found(candidate)
                    print(f"{GREEN}[OK] Yayın bulundu: {candidate}{RESET}")
                    dur_event.set()
                    return (i, candidate)
                else:
                    print(f"{YELLOW}[-] {candidate} aktif ama yayın linki yok.{RESET}")
            else:
                # opsiyonel: sessiz bırakmak istersen bu satırı yorum satırı yap
                print(f"{RED}[-] {candidate} yanıt kodu {r.status_code}.{RESET}")
        except requests.RequestException:
            # erişilemediğini sessizce geçebilirsin
            # print(f"{RED}[-] {candidate} erişilemedi.{RESET}")
            pass
    return None

def siteyi_bul_otomatik():
    start = read_last_index() or DEFAULT_START
    print(f"{GREEN}[*] Arama başlatılıyor, başlangıç index: {start}{RESET}")
    empty_batches = 0
    i = start
    while not dur_event.is_set():
        with ThreadPoolExecutor(max_workers=THREAD_SAYISI) as executor:
            futures = {executor.submit(kontrol_et, x): x for x in range(i, i + BATCH_SIZE)}
            for future in as_completed(futures):
                idx = futures[future]
                write_last_index(idx)
                res = future.result()
                if res:
                    write_last_index(res[0])
                    return res[1]
        i += BATCH_SIZE
        empty_batches += 1
        if MAX_EMPTY_BATCHES and empty_batches >= MAX_EMPTY_BATCHES:
            print(f"{YELLOW}[Uyarı] Maksimum deneme sayısına ulaşıldı.{RESET}")
            return None
        write_last_index(i)
        time.sleep(SLEEP_BETWEEN_BATCHES)
    return None

def find_baseurl(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        return None
    m = re.search(r'baseurl\s*[:=]\s*["\']([^"\']+)["\']', r.text)
    return m.group(1) if m else None

def generate_m3u(base_url, referer, ua):
    lines = ["#EXTM3U"]
    for idx, k in enumerate(KANALLAR, 1):
        name = k["kanal_adi"]
        lines.append(f'#EXTINF:-1 tvg-id="{k["tvg_id"]}" tvg-name="{name}",{name}')
        lines.append(f'#EXTVLCOPT:http-user-agent={ua}')
        lines.append(f'#EXTVLCOPT:http-referrer={referer}')
        lines.append(base_url + k["dosya"])
        print(f"  ✔ {idx:02d}. {name}")
    return "\n".join(lines)

if __name__ == "__main__":
    try:
        site = siteyi_bul_otomatik()
        if not site:
            print(f"{RED}[HATA] Aktif site bulunamadı.{RESET}")
            sys.exit(1)

        channel_url = site.rstrip("/") + "/channel.html?id=yayinzirve"
        base_url = find_baseurl(channel_url)
        if not base_url:
            print(f"{RED}[HATA] Base URL bulunamadı.{RESET}")
            sys.exit(1)

        playlist = generate_m3u(base_url, site, "Mozilla/5.0")
        with open("trgoalas.m3u", "w", encoding="utf-8") as f:
            f.write(playlist)

        print(f"{GREEN}[OK] Playlist oluşturuldu: trgoalas.m3u{RESET}")

    except KeyboardInterrupt:
        print(f"\n{YELLOW}[İptal edildi] Son index kaydediliyor...{RESET}")
        sys.exit(0)
# Güncelleme: Mon Oct 27 12:34:15 UTC 2025
# Güncelleme: Mon Oct 27 12:41:06 UTC 2025
# Güncelleme: Mon Oct 27 12:43:19 UTC 2025
# Güncelleme: Mon Oct 27 12:44:12 UTC 2025
# Güncelleme: Mon Oct 27 13:35:17 UTC 2025
# Güncelleme: Mon Oct 27 14:24:58 UTC 2025
# Güncelleme: Mon Oct 27 15:25:03 UTC 2025
# Güncelleme: Mon Oct 27 16:31:18 UTC 2025
# Güncelleme: Mon Oct 27 17:20:17 UTC 2025
# Güncelleme: Mon Oct 27 18:34:07 UTC 2025
# Güncelleme: Mon Oct 27 19:18:47 UTC 2025
# Güncelleme: Mon Oct 27 20:23:37 UTC 2025
# Güncelleme: Mon Oct 27 21:19:48 UTC 2025
# Güncelleme: Mon Oct 27 22:21:03 UTC 2025
