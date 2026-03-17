#!/usr/bin/env python
"""Test script to verify category news fetching"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime

def test_fetch_rss(category):
    """Test fetching RSS for a specific category"""
    
    TOPIC_MAP = {
        'travel': 'https://news.google.com/rss/search?q=Travel',
        'food': 'https://news.google.com/rss/search?q=Food',
        'sports': 'https://news.google.com/rss/headlines/section/topic/SPORTS',
        'tech': 'https://news.google.com/rss/headlines/section/topic/TECHNOLOGY',
    }
    
    category_lower = category.lower()
    
    if category_lower in TOPIC_MAP:
        url = TOPIC_MAP[category_lower]
    else:
        url = f"https://news.google.com/rss/search?q={category}"
    
    print(f"\n{'='*60}")
    print(f"Testing category: {category}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")
    
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        
        root = ET.fromstring(res.text)
        items = root.findall('.//item')
        
        print(f"✓ Successfully fetched {len(items)} articles\n")
        
        # Show first 3 articles
        for i, item in enumerate(items[:3], 1):
            title = item.find('title').text if item.find('title') is not None else 'No title'
            print(f"{i}. {title}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    categories = ['Travel', 'Food', 'Sports', 'Tech', 'Health', 'Music']
    
    results = {}
    for cat in categories:
        results[cat] = test_fetch_rss(cat)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for cat, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{cat:15} {status}")
