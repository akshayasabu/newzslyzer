import requests
import xml.etree.ElementTree as ET

def fetch_gn_rss(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        res = requests.get(url, headers=headers, timeout=12)
        res.raise_for_status()
        root = ET.fromstring(res.text)
        items = root.findall('.//item')
        return len(items)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    urls = [
        'https://news.google.com/rss/headlines/section/topic/WORLD',
        'https://news.google.com/rss/search?q=Kerala+News',
        'https://news.google.com/rss/headlines/section/topic/SPORTS'
    ]
    for url in urls:
        print(f"URL: {url} | Found: {fetch_gn_rss(url)}")
