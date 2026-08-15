import re
import os
import requests
import yt_dlp

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://tivi6.com.tr/"
}

def resolve_stream_url(url):
    """Gelen bağlantı türüne göre canlı yayın m3u8 adresini çözer."""
    
    # 1. Doğrudan m3u8 veya mpd bağlantısı ise direkt dön
    if ".m3u8" in url or ".mpd" in url:
        return url

    # 2. Cine1 Altyapısı
    if "cine1.com.tr" in url:
        try:
            r = requests.get("https://cine1.com.tr/", headers=headers, timeout=10)
            match = re.search(r'(https://canliyayin\.cine1\.com\.tr/memfs/[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', r.text)
            if match:
                return match.group(1).replace("&amp;", "&")
        except Exception as e:
            print(f"Cine1 hatası: {e}")
        return None

    # 3. Tivi6 Özel Ayrıştırıcısı
    if "tivi6.com.tr" in url:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            # Sayfa içinde iFrame veya doğrudan m3u8 arama
            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', r.text)
            target_text = r.text
            
            # Eğer oyuncu iFrame içindeyse o iFrame adresine istek atıp m3u8 arayalım
            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith("//"):
                    iframe_url = "https:" + iframe_url
                elif iframe_url.startswith("/"):
                    iframe_url = "https://tivi6.com.tr" + iframe_url
                r_iframe = requests.get(iframe_url, headers=headers, timeout=10)
                target_text = r_iframe.text

            # m3u8 URL bulma
            match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', target_text)
            if match:
                return match.group(1).replace("&amp;", "&")
        except Exception as e:
            print(f"Tivi6 hatası: {e}")

    # 4. YouTube / Dailymotion / Genel Video Platformları (yt-dlp)
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

    # 5. Genel Regex Taraması (Diğer siteler için varsayılan)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', r.text)
        if match:
            return match.group(1).replace("&amp;", "&")
    except Exception as e:
        print(f"Genel regex hatası ({url}): {e}")

    return None
