import re
import os
import requests
import yt_dlp

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.cnnturk.com/"
}

def resolve_stream_url(url):
    """Gelen bağlantı türüne göre canlı yayın m3u8 adresini çözer."""
    
    # 1. Doğrudan m3u8, mpd veya bilinen canlı akış CDN linki ise DİREKT DÖN (Hiç tarama yapma)
    if ".m3u8" in url or ".mpd" in url or "artidijitalmedya.com" in url:
        return url

    # 2. Cine1 Altyapısı (Otomatik dinamik session çözücü)
    if "cine1.com.tr" in url:
        try:
            r = requests.get("https://cine1.com.tr/", headers=headers, timeout=10)
            match = re.search(r'(https://canliyayin\.cine1\.com\.tr/memfs/[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', r.text)
            if match:
                return match.group(1).replace("&amp;", "&")
        except Exception as e:
            print(f"Cine1 hatası: {e}")
        return None

    # 3. Duhnet / CNN Türk / Kanal D Altyapısı (API + Regex Çözücü)
    if "cnnturk" in url or "duhnet" in url:
        try:
            # a) Doğrudan CNN Türk'ün canlı yayın servis API'sinden taze token'lı linki çekmeyi dene
            api_url = "https://www.cnnturk.com/api/v1/live/stream"
            r_api = requests.get(api_url, headers=headers, timeout=5)
            if r_api.status_code == 200:
                data = r_api.json()
                # JSON içinde stream URL varsa onu döndür
                if isinstance(data, dict) and "data" in data and "streamUrl" in data["data"]:
                    return data["data"]["streamUrl"]

            # b) API yanıt vermezse web sayfasını tara
            r = requests.get(url, headers=headers, timeout=10)
            
            # Token'lı duhnet m3u8 linki ara (?st= veya &st= içeren)
            match_token = re.search(r'(https?://[^\s"\'<>]*duhnet\.tv[^\s"\'<>]*\.m3u8\?[^\s"\'<>]+)', r.text)
            if match_token:
                return match_token.group(1).replace("&amp;", "&")

            # Token'sız yalın m3u8 linki ara
            match_plain = re.search(r'(https?://[^\s"\'<>]*duhnet\.tv[^\s"\'<>]*\.m3u8[^\s"\'<>]*)', r.text)
            if match_plain:
                return match_plain.group(1).replace("&amp;", "&")

        except Exception as e:
            print(f"Duhnet/CNN Türk çözme hatası: {e}")

    # 4. YouTube / Dailymotion Canlı Yayınları (yt-dlp)
    if "youtube.com" in url or "youtu.be" in url or "dailymotion.com" in url:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'http_headers': headers
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info.get('url')
        except Exception as e:
            print(f"yt-dlp hatası ({url}): {e}")
        return None

    # 5. Genel Regex Taraması (Web sitelerindeki gömülü m3u8 linklerini arar)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', r.text)
        if match:
            return match.group(1).replace("&amp;", "&")
    except Exception as e:
        print(f"Genel regex hatası ({url}): {e}")

    return None

def main():
    if not os.path.exists("channels.txt"):
        print("[HATA] channels.txt dosyası bulunamadı!")
        return

    m3u_lines = ["#EXTM3U\n"]

    with open("channels.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [p.strip() for p in line.split("|")]
        name = parts[0]
        url = parts[1]
        group = parts[2] if len(parts) > 2 and parts[2] else "Genel"
        logo = parts[3] if len(parts) > 3 and parts[3] else ""

        print(f"[{name}] İşleniyor...")
        stream_url = resolve_stream_url(url)

        if stream_url:
            m3u_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}')
            m3u_lines.append(f'{stream_url}\n')
            print(f"  -> Başarılı: {stream_url[:60]}...")
        else:
            print("  -> BAŞARISIZ! Bağlantı çözülemedi.")

    # Ana dizinde playlist.m3u oluştur
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

if __name__ == "__main__":
    main()
