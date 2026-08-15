import re
import requests

def get_cine1_stream():
    url = "https://cine1.com.tr/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://cine1.com.tr/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # HTML veya JS içindeki canliyayin.cine1.com.tr m3u8 adresini ayıklar
            pattern = r'(https://canliyayin\.cine1\.com\.tr/memfs/[^\s"\'<>]+\.m3u8[^\s"\'<>]*)'
            match = re.search(pattern, response.text)
            
            if match:
                stream_url = match.group(1)
                # HTML entity kaçış karakterlerini temizle (&amp; -> &)
                stream_url = stream_url.replace("&amp;", "&")
                return stream_url
            else:
                print("[HATA] m3u8 bağlantısı sayfa kaynağında bulunamadı.")
        else:
            print(f"[HATA] Siteye erişilemedi. HTTP Kodu: {response.status_code}")
    except Exception as e:
        print(f"[HATA] İstek sırasında bir hata oluştu: {e}")

    return None

def generate_m3u():
    stream_url = get_cine1_stream()
    
    if not stream_url:
        print("[BAŞARISIZ] Yayın adresi alınamadı, dosya güncellenmedi.")
        return

    print(f"[BAŞARILI] Güncel Yayın Adresi: {stream_url}")

    m3u_content = [
        "#EXTM3U",
        '#EXTINF:-1 tvg-name="Cine1" tvg-logo="https://cine1.com.tr/logo.png" group-title="Ulusal",Cine1',
        stream_url
    ]

    with open("cine1.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))

if __name__ == "__main__":
    generate_m3u()
