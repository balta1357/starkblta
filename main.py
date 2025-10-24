# main.py
from datetime import datetime

# Kanal isimleri ve linkleri
channels = {
    "SifirTV": "https://www.youtube.com/watch?v=JCSOAmBeXnY",
    "ASpor": "https://www.youtube.com/watch?v=ysh-bPiD3Oo",
    "HTSpor": "https://www.youtube.com/watch?v=RdpqsTbi_KU",
    "NTV Spor": "https://www.youtube.com/watch?v=pqq5c6k70kk",
    "CNN Turk": "https://www.youtube.com/watch?v=6N8_r2uwLEc",
    "SozcuTV": "https://www.youtube.com/watch?v=ztmY_cCtUl0",
    "HalkTV": "https://www.youtube.com/watch?v=VBU0QX6brew",
    "Haberturk": "https://www.youtube.com/watch?v=RNVNlJSUFoE",
    "Tele1": "https://www.youtube.com/watch?v=elQyWeeDCYU",
    "AHaber": "https://www.youtube.com/watch?v=nmY9i63t6qo",
    "7/24 | Arzu Film": "https://www.youtube.com/watch?v=Pq7ndgZHjjE",
    "NTV": "https://www.youtube.com/watch?v=pqq5c6k70kk",
    "Kemal Sunal": "https://www.youtube.com/watch?v=-2L6D9gil8w",
    "BS Haber": "https://www.youtube.com/watch?v=ovXYPBAzo-w",
    "Zeki": "https://www.youtube.com/watch?v=dB9XP3GlrmI",
    "Sunal": "https://www.youtube.com/watch?v=hfx8H7YrmTw",
    "TV100": "https://www.youtube.com/watch?v=6g_DvD8e2T0",
    "Haber Global": "https://www.youtube.com/watch?v=EqoCJ8BPxtE",
    "TGRT": "https://www.youtube.com/watch?v=TsB0xYOH0AU",
    "Ekol": "https://www.youtube.com/watch?v=Pyqj8qGL500",
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
m3u_filename = f"youtube_live_{timestamp}.m3u"

with open(m3u_filename, "w") as f:
    f.write("#EXTM3U\n")
    for name, url in channels.items():
        if url.strip():  # boş linkleri atla
            f.write(f"#EXTINF:-1,{name}\n")
            f.write(f"{url}\n")

print(f"[OK] {m3u_filename} oluşturuldu.")
