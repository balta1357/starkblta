import requests
import time
import re

def getAuthSignature():
    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip"
    }
    data = {
        "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
        "reason": "app-blur",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {
                "type": "Handset",
                "os": "Android",
                "osVersion": "10",
                "model": "Pixel 4",
                "brand": "Google"
            }
        }
    }
    resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=10)
    return resp.json().get("signature")

def vavoo_groups():
    return [""]

def clean_channel_name(name):
    return re.sub(r'\s*\.(a|b|c|s|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|t|u|v|w|x|y|z)\s*$', '', name, flags=re.IGNORECASE).strip()

def get_channels():
    signature = getAuthSignature()
    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip",
        "mediahubmx-signature": signature
    }
    all_channels = []
    for group in vavoo_groups():
        cursor = 0
        while True:
            data = {
                "language": "de",
                "region": "AT",
                "catalogId": "iptv",
                "id": "iptv",
                "adult": False,
                "search": "",
                "sort": "name",
                "filter": {"group": group},
                "cursor": cursor,
                "clientVersion": "3.0.2"
            }
            resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=data, headers=headers, timeout=10)
            r = resp.json()
            items = r.get("items", [])
            all_channels.extend(items)
            cursor = r.get("nextCursor")
            if not cursor:
                break
    return all_channels

def save_as_m3u(channels, filename="vavoo.m3u"):
    all_channels_flat = []
    for ch in channels:
        original_name = ch.get("name", "SenzaNome")
        name = clean_channel_name(original_name)
        url = ch.get("url", "")
        # 🔁 URL DEĞİŞİKLİĞİ BURADA
        url = url.replace("https://vavoo.to/vavoo-iptv/play/", "https://cors-anywhere.yidianzhishi.cn/https://goldvod.org/tv/vavoo?id=")
        category = ch.get("group", "Generale")
        if url:
            all_channels_flat.append({'name': name, 'url': url, 'category': category})

    name_counts = {}
    for ch_data in all_channels_flat:
        name_counts[ch_data['name']] = name_counts.get(ch_data['name'], 0) + 1

    final_channels_data = []
    name_counter = {}
    for ch_data in all_channels_flat:
        name = ch_data['name']
        if name_counts[name] > 1:
            if name not in name_counter:
                name_counter[name] = 1
                new_name = name
            else:
                name_counter[name] += 1
                new_name = f"{name} ({name_counter[name]})"
        else:
            new_name = name
        final_channels_data.append({'name': new_name, 'url': ch_data['url'], 'category': ch_data['category']})

    channels_by_category = {}
    for ch_data in final_channels_data:
        category = ch_data['category']
        if category not in channels_by_category:
            channels_by_category[category] = []
        channels_by_category[category].append((ch_data['name'], ch_data['url']))

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category in sorted(channels_by_category.keys()):
            channel_list = sorted(channels_by_category[category], key=lambda x: x[0].lower())
            f.write(f"\n# {category.upper()}\n")
            for name, url in channel_list:
                f.write(f'#EXTINF:-1 group-title="{category} VAVOO",{name}\n{url}\n')

    print(f"✅ Playlist M3U kaydedildi: {filename}")
    print(f"📺 Kategorilere göre dağılım ({len(channels_by_category)} kategori):")
    for category, channel_list in channels_by_category.items():
        print(f"  - {category}: {len(channel_list)} kanal")

def main():
    print("🎬 Kanal listesi çekiliyor...")
    channels = get_channels()
    print(f"🔢 Toplam {len(channels)} kanal bulundu. Playlist oluşturuluyor...")
    save_as_m3u(channels)

if __name__ == "__main__":
    main()
